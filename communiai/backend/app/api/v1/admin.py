"""Administrator endpoints: users, system health, AI monitoring, errors, runtime settings.

Admins do NOT see project content by default. Content access requires the student's time-limited
support permission plus a stated reason, and every access is written to the audit log.
"""
import uuid
from datetime import UTC, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.api.deps import Page, audit, require_admin
from app.core.config import get_settings
from app.core.database import get_db
from app.core.errors import AppError, not_found
from app.models import (
    AIJob, AIRequestLog, AuditLog, DefenseSession, JobStatus, Project, User, utcnow,
)
from app.schemas import AdminProjectAccessIn, AdminSettingIn
from app.services.system_settings import EDITABLE_SETTINGS, all_settings, set_setting

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/users")
def users(page: Page = Depends(), q: str | None = None, admin: User = Depends(require_admin),
          db: Session = Depends(get_db)):
    stmt = select(User)
    if q:
        stmt = stmt.where(User.email.ilike(f"%{q[:100]}%"))
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = db.scalars(stmt.order_by(User.created_at.desc()).offset(page.offset).limit(page.page_size)).all()
    items = []
    for u in rows:
        items.append({
            "id": str(u.id), "first_name": u.first_name, "last_name": u.last_name, "email": u.email,
            "university": u.university, "study_program": u.study_program, "role": u.role.value,
            "is_active": u.is_active, "created_at": u.created_at.isoformat(),
            "projects_count": db.scalar(select(func.count()).select_from(Project).where(
                Project.owner_id == u.id, Project.deleted_at.is_(None))) or 0,
            "defenses_count": db.scalar(select(func.count()).select_from(DefenseSession)
                                        .where(DefenseSession.user_id == u.id)) or 0,
            "support_access_active": bool(u.support_access_until and
                                          u.support_access_until.replace(tzinfo=u.support_access_until.tzinfo or UTC) > utcnow()),
        })
    return page.wrap(items, total)


@router.patch("/users/{user_id}")
def set_user_active(user_id: uuid.UUID, is_active: bool, admin: User = Depends(require_admin),
                    db: Session = Depends(get_db)):
    u = db.get(User, user_id)
    if u is None:
        raise not_found("Foydalanuvchi")
    if u.id == admin.id:
        raise AppError(400, "SELF_CHANGE", "O'z hisobingizni o'chira olmaysiz")
    u.is_active = is_active
    audit(db, admin.id, "admin.user_active", "user", u.id, {"is_active": is_active})
    db.commit()
    return {"id": str(u.id), "is_active": u.is_active}


@router.get("/system")
def system_status(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    s = get_settings()
    db_ok = True
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_ok = False
    since = utcnow() - timedelta(hours=24)
    jobs_by_status = dict(db.execute(select(AIJob.status, func.count()).where(AIJob.created_at >= since)
                                     .group_by(AIJob.status)).all())
    ai_stats = db.execute(select(func.count(), func.avg(AIRequestLog.latency_ms)).where(
        AIRequestLog.created_at >= since)).one()
    ai_errors = db.scalar(select(func.count()).select_from(AIRequestLog).where(
        AIRequestLog.created_at >= since, AIRequestLog.status != "ok")) or 0
    return {
        "app_env": s.APP_ENV, "database": "ok" if db_ok else "error",
        "ai": {"provider": s.AI_PROVIDER, "configured": s.ai_configured, "model": all_settings().get("ai_model") or s.AI_MODEL,
               "timeout_seconds": s.AI_TIMEOUT_SECONDS},
        "email_configured": s.email_enabled, "storage_backend": s.FILE_STORAGE_BACKEND,
        "rubric_version": s.RUBRIC_VERSION,
        "users_total": db.scalar(select(func.count()).select_from(User)) or 0,
        "last_24h": {
            "jobs": {k.value if hasattr(k, "value") else k: v for k, v in jobs_by_status.items()},
            "ai_requests": ai_stats[0] or 0, "ai_avg_latency_ms": int(ai_stats[1] or 0), "ai_errors": ai_errors,
        },
        "settings": all_settings(),
    }


@router.get("/ai-requests")
def ai_requests(page: Page = Depends(), admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    stmt = select(AIRequestLog)
    total = db.scalar(select(func.count()).select_from(AIRequestLog))
    rows = db.scalars(stmt.order_by(AIRequestLog.created_at.desc()).offset(page.offset).limit(page.page_size)).all()
    return page.wrap([{"id": str(r.id), "operation": r.operation, "provider": r.provider, "model": r.model,
                       "status": r.status, "latency_ms": r.latency_ms, "input_tokens": r.input_tokens,
                       "output_tokens": r.output_tokens, "error_type": r.error_type,
                       "created_at": r.created_at.isoformat()} for r in rows], total)


@router.get("/errors")
def errors(page: Page = Depends(), admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    stmt = select(AIJob).where(AIJob.status == JobStatus.FAILED)
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = db.scalars(stmt.order_by(AIJob.created_at.desc()).offset(page.offset).limit(page.page_size)).all()
    return page.wrap([{"id": str(j.id), "kind": j.kind, "error_code": j.error_code, "error_message": j.error_message,
                       "created_at": j.created_at.isoformat()} for j in rows], total)


@router.get("/settings")
def get_settings_view(admin: User = Depends(require_admin)):
    return {"settings": all_settings(),
            "editable": {k: {"type": t.__name__, "description": d} for k, (t, d) in EDITABLE_SETTINGS.items()}}


@router.put("/settings")
def put_setting(body: AdminSettingIn, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    if body.key not in EDITABLE_SETTINGS:
        raise AppError(400, "UNKNOWN_SETTING", "Bunday sozlama mavjud emas")
    typ = EDITABLE_SETTINGS[body.key][0]
    if not isinstance(body.value, typ):
        raise AppError(422, "VALIDATION_ERROR", f"Qiymat turi {typ.__name__} bo'lishi kerak")
    set_setting(body.key, body.value, admin.id)
    audit(db, admin.id, "admin.setting", "system_setting", None, {"key": body.key, "value": body.value})
    db.commit()
    return {"settings": all_settings()}


@router.post("/projects/{project_id}/access")
def access_project(project_id: uuid.UUID, body: AdminProjectAccessIn, admin: User = Depends(require_admin),
                   db: Session = Depends(get_db)):
    p = db.get(Project, project_id)
    if p is None or p.deleted_at is not None:
        raise not_found("Loyiha")
    owner = db.get(User, p.owner_id)
    until = owner.support_access_until
    if until is None or (until if until.tzinfo else until.replace(tzinfo=UTC)) < utcnow():
        audit(db, admin.id, "admin.project_access_denied", "project", p.id, {"reason": body.reason})
        db.commit()
        raise AppError(403, "ACCESS_NOT_GRANTED", "Talaba texnik yordam uchun ruxsat bermagan")
    audit(db, admin.id, "admin.project_access", "project", p.id, {"reason": body.reason, "owner_id": str(owner.id)})
    db.commit()
    return {"id": str(p.id), "title": p.title, "description": p.description, "problem": p.problem,
            "files": [{"filename": f.original_filename, "extraction_status": f.extraction_status.value,
                       "extraction_error": f.extraction_error} for f in p.files]}


@router.get("/audit-logs")
def audit_logs(page: Page = Depends(), admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    stmt = select(AuditLog).where(AuditLog.action.like("admin.%"))
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = db.scalars(stmt.order_by(AuditLog.created_at.desc()).offset(page.offset).limit(page.page_size)).all()
    return page.wrap([{"id": str(r.id), "actor_id": str(r.actor_id) if r.actor_id else None, "action": r.action,
                       "resource_type": r.resource_type, "resource_id": r.resource_id, "details": r.details,
                       "created_at": r.created_at.isoformat()} for r in rows], total)
