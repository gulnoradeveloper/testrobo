import hashlib
import uuid

from fastapi import APIRouter, Depends, File, Response, UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import (
    IdempotencyKey, Page, ai_rate_limit, audit, get_current_user, idem_get, idem_save, owned_project,
    require_ai_consent,
)
from app.core.config import get_settings
from app.core.database import get_db
from app.core.errors import AppError, not_found
from app.models import (
    AnalysisStatus, CompetencyResult, DefenseSession, ExtractionStatus, Project, ProjectAnalysis, ProjectFile,
    User, utcnow,
)
from app.schemas import ProjectCreate, ProjectUpdate
from app.services import jobs
from app.services.ai.prompts import PROMPT_VERSION
from app.services.ai.provider import get_provider
from app.services.projects.context import has_minimum_data, snapshot_hash
from app.services.projects.extraction import UploadRejected, extract_text, safe_filename, validate_upload
from app.services.storage import get_storage

router = APIRouter(tags=["Projects"])

PROJECT_FIELDS = ("title", "description", "problem", "objective", "target_users", "features", "technologies",
                  "innovation", "expected_results", "future_plans")


def file_view(f: ProjectFile) -> dict:
    return {"id": str(f.id), "original_filename": f.original_filename, "mime_type": f.mime_type,
            "file_size": f.file_size, "extraction_status": f.extraction_status.value,
            "extraction_error": f.extraction_error,
            "extracted_chars": len(f.extracted_text or ""),
            "extracted_preview": (f.extracted_text or "")[:500], "created_at": f.created_at.isoformat()}


def analysis_view(a: ProjectAnalysis, current_hash: str | None = None, job=None) -> dict:
    return {"id": str(a.id), "project_id": str(a.project_id), "status": a.status.value, "ai_model": a.ai_model,
            "prompt_version": a.prompt_version, "input_snapshot_hash": a.input_snapshot_hash,
            "is_outdated": current_hash is not None and current_hash != a.input_snapshot_hash,
            "result": a.result_json, "error_message": a.error_message, "created_at": a.created_at.isoformat(),
            "job": jobs.job_view(job)}


def project_view(db: Session, p: Project, detail: bool = False) -> dict:
    data = {"id": str(p.id), "category": p.category.value, "created_at": p.created_at.isoformat(),
            "updated_at": p.updated_at.isoformat() if p.updated_at else None,
            **{k: getattr(p, k) for k in PROJECT_FIELDS}}
    data["files_count"] = len(p.files)
    data["defenses_count"] = db.scalar(select(func.count()).select_from(DefenseSession)
                                       .where(DefenseSession.project_id == p.id)) or 0
    if detail:
        current = snapshot_hash(p)
        data["files"] = [file_view(f) for f in p.files]
        last = db.scalars(select(ProjectAnalysis).where(ProjectAnalysis.project_id == p.id)
                          .order_by(ProjectAnalysis.created_at.desc())).first()
        data["latest_analysis"] = analysis_view(last, current, jobs.active_job(db, last.id, ("project_analysis",))) \
            if last else None
        sessions = db.scalars(select(DefenseSession).where(DefenseSession.project_id == p.id)
                              .order_by(DefenseSession.created_at.desc()).limit(20)).all()
        hist = []
        for s in sessions:
            r = db.scalars(select(CompetencyResult).where(CompetencyResult.session_id == s.id)).first()
            hist.append({"id": str(s.id), "mode": s.mode.value, "status": s.status.value,
                         "question_limit": s.question_limit, "created_at": s.created_at.isoformat(),
                         "total_score": r.total_score if r else None,
                         "max_applicable_score": r.max_applicable_score if r else None,
                         "level": r.level if r else None})
        data["defenses"] = hist
        data["snapshot_hash"] = current
    return data


# ------------------------------------------------------------------ projects
@router.get("/projects")
def list_projects(page: Page = Depends(), q: str | None = None, user: User = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    stmt = select(Project).where(Project.owner_id == user.id, Project.deleted_at.is_(None))
    if q:
        stmt = stmt.where(Project.title.ilike(f"%{q[:100]}%"))
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    items = db.scalars(stmt.order_by(Project.updated_at.desc()).offset(page.offset).limit(page.page_size)).all()
    return page.wrap([project_view(db, p) for p in items], total)


@router.post("/projects", status_code=201)
def create_project(body: ProjectCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    p = Project(owner_id=user.id, **body.model_dump())
    db.add(p)
    db.flush()
    audit(db, user.id, "project.create", "project", p.id)
    db.commit()
    db.refresh(p)
    return project_view(db, p, detail=True)


@router.get("/projects/{project_id}")
def get_project(project_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return project_view(db, owned_project(db, project_id, user), detail=True)


@router.patch("/projects/{project_id}")
def update_project(project_id: uuid.UUID, body: ProjectUpdate, user: User = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    p = owned_project(db, project_id, user)
    changes = body.model_dump(exclude_unset=True)
    for k, v in changes.items():
        if v is None and k in ("title", "category", "description", "problem"):
            raise AppError(422, "VALIDATION_ERROR", f"{k} majburiy maydon")
        setattr(p, k, v if v is not None else "")
    audit(db, user.id, "project.update", "project", p.id, {"fields": sorted(changes)})
    db.commit()
    db.refresh(p)
    return project_view(db, p, detail=True)


@router.delete("/projects/{project_id}", status_code=204)
def delete_project(project_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    p = owned_project(db, project_id, user)
    storage = get_storage()
    for f in list(p.files):
        storage.delete(f.storage_key)
        f.extracted_text = None
        db.delete(f)
    p.deleted_at = utcnow()
    audit(db, user.id, "project.delete", "project", p.id)
    db.commit()
    return Response(status_code=204)


# ------------------------------------------------------------------ files
@router.post("/projects/{project_id}/files", status_code=201)
async def upload_file(project_id: uuid.UUID, file: UploadFile = File(...), user: User = Depends(get_current_user),
                      db: Session = Depends(get_db)):
    p = owned_project(db, project_id, user)
    s = get_settings()
    if len(p.files) >= 20:
        raise AppError(409, "TOO_MANY_FILES", "Bitta loyiha uchun ko'pi bilan 20 ta fayl yuklash mumkin")
    data = await file.read(s.max_upload_bytes + 1)
    name = safe_filename(file.filename or "fayl")
    try:
        ext, mime = validate_upload(name, file.content_type, data)
    except UploadRejected as e:
        status = 413 if e.code == "FILE_TOO_LARGE" else 415 if e.code in ("UNSUPPORTED_TYPE", "MIME_MISMATCH") else 400
        raise AppError(status, e.code, e.message) from None
    digest = hashlib.sha256(data).hexdigest()
    dup = next((f for f in p.files if f.sha256 == digest), None)
    if dup is not None:  # same content uploaded twice (e.g. double tap) -> return existing
        return file_view(dup)
    result = extract_text(ext, data)
    key = get_storage().save(data, ext)
    f = ProjectFile(project_id=p.id, original_filename=name, storage_key=key, mime_type=mime, file_size=len(data),
                    sha256=digest, extraction_status=ExtractionStatus(result.status),
                    extraction_error=result.error, extracted_text=result.text or None)
    db.add(f)
    p.updated_at = utcnow()
    audit(db, user.id, "file.upload", "project_file", None, {"project_id": str(p.id), "size": len(data)})
    db.commit()
    db.refresh(f)
    return file_view(f)


@router.get("/projects/{project_id}/files")
def list_files(project_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    p = owned_project(db, project_id, user)
    return {"items": [file_view(f) for f in p.files]}


@router.delete("/projects/{project_id}/files/{file_id}", status_code=204)
def delete_file(project_id: uuid.UUID, file_id: uuid.UUID, user: User = Depends(get_current_user),
                db: Session = Depends(get_db)):
    p = owned_project(db, project_id, user)
    f = next((x for x in p.files if x.id == file_id), None)
    if f is None:
        raise not_found("Fayl")
    get_storage().delete(f.storage_key)
    p.files.remove(f)
    p.updated_at = utcnow()
    audit(db, user.id, "file.delete", "project_file", file_id, {"project_id": str(p.id)})
    db.commit()
    return Response(status_code=204)


# ------------------------------------------------------------------ analysis
@router.post("/projects/{project_id}/analyze", status_code=202, dependencies=[Depends(ai_rate_limit)])
def analyze(project_id: uuid.UUID, force: bool = False, idem_key: str | None = IdempotencyKey,
            user: User = Depends(require_ai_consent), db: Session = Depends(get_db)):
    endpoint = f"analyze:{project_id}"
    prev = idem_get(db, user, idem_key, endpoint)
    if prev:
        return prev.response_json
    p = owned_project(db, project_id, user)
    missing = has_minimum_data(p)
    if missing:
        raise AppError(422, "PROJECT_INCOMPLETE", "Loyiha ma'lumotlari yetarli emas", {"missing": missing})
    h = snapshot_hash(p)
    # Reuse a running or completed analysis for the same project version (avoids duplicate AI cost).
    existing = db.scalars(select(ProjectAnalysis).where(
        ProjectAnalysis.project_id == p.id, ProjectAnalysis.input_snapshot_hash == h,
        ProjectAnalysis.status.in_([AnalysisStatus.PENDING, AnalysisStatus.COMPLETED]),
    ).order_by(ProjectAnalysis.created_at.desc())).first()
    if existing and (existing.status == AnalysisStatus.PENDING or not force):
        job = jobs.active_job(db, existing.id, ("project_analysis",))
        if existing.status == AnalysisStatus.PENDING and job is None:
            job = jobs.create_job(db, user_id=user.id, kind="project_analysis", resource_type="project_analysis",
                                  resource_id=existing.id)
            db.commit()
            jobs.dispatch(job.id)
            db.expire_all()
            db.refresh(existing)
        return analysis_view(existing, h, job)
    a = ProjectAnalysis(project_id=p.id, input_snapshot_hash=h, ai_model=get_provider().model,
                        prompt_version=PROMPT_VERSION, status=AnalysisStatus.PENDING)
    db.add(a)
    db.flush()
    job = jobs.create_job(db, user_id=user.id, kind="project_analysis", resource_type="project_analysis",
                          resource_id=a.id)
    body = analysis_view(a, h, job)
    idem_save(db, user, idem_key, endpoint, 202, body)
    audit(db, user.id, "analysis.request", "project_analysis", a.id, {"project_id": str(p.id)})
    db.commit()
    jobs.dispatch(job.id)
    db.expire_all()
    db.refresh(a)
    db.refresh(job)
    return analysis_view(a, h, job)


@router.get("/projects/{project_id}/analyses")
def list_analyses(project_id: uuid.UUID, page: Page = Depends(), user: User = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    p = owned_project(db, project_id, user)
    h = snapshot_hash(p)
    stmt = select(ProjectAnalysis).where(ProjectAnalysis.project_id == p.id)
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = db.scalars(stmt.order_by(ProjectAnalysis.created_at.desc()).offset(page.offset).limit(page.page_size)).all()
    return page.wrap([analysis_view(a, h) for a in rows], total)


@router.get("/analyses/{analysis_id}")
def get_analysis(analysis_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    a = db.get(ProjectAnalysis, analysis_id)
    if a is None:
        raise not_found("Ekspertiza")
    p = owned_project(db, a.project_id, user)
    return analysis_view(a, snapshot_hash(p), jobs.active_job(db, a.id, ("project_analysis",)))
