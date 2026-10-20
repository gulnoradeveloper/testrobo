from datetime import timedelta

from fastapi import APIRouter, Depends, Response
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.api.deps import Page, audit, get_current_user
from app.core.database import get_db
from app.core.errors import AppError
from app.core.security import hash_password, password_problems, verify_password
from app.models import (
    AuditLog, CompetencyResult, DefenseAnswer, DefenseQuestion, DefenseSession, ImprovementPlan, PracticeAttempt,
    Project, ProjectAnalysis, RefreshToken, SessionStatus, User, utcnow,
)
from app.schemas import ChangePasswordIn, ProfileUpdateIn, UserOut
from app.services.storage import get_storage

router = APIRouter(prefix="/me", tags=["Profile & Analytics"])

ACTIVITY_LABELS = {
    "user.register": "Ro'yxatdan o'tildi", "user.login": "Tizimga kirildi", "project.create": "Loyiha yaratildi",
    "project.update": "Loyiha tahrirlandi", "project.delete": "Loyiha o'chirildi", "file.upload": "Fayl yuklandi",
    "file.delete": "Fayl o'chirildi", "analysis.request": "AI ekspertiza so'raldi", "defense.create": "Himoya yaratildi",
    "defense.start": "Himoya boshlandi", "defense.complete": "Himoya yakunlandi", "defense.cancel": "Himoya bekor qilindi",
    "practice.attempt": "Qayta mashq topshirildi", "user.consent": "AI roziligi yangilandi",
    "user.profile_update": "Profil yangilandi", "user.password_change": "Parol o'zgartirildi",
    "user.support_access": "Texnik yordam ruxsati yangilandi",
}


@router.get("", response_model=UserOut)
def get_me(user: User = Depends(get_current_user)):
    return user


@router.patch("", response_model=UserOut)
def update_me(body: ProfileUpdateIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    data = body.model_dump(exclude_unset=True)
    for k in ("first_name", "last_name", "university", "study_program"):
        if data.get(k) is not None:
            setattr(user, k, data[k])
    if "ai_consent" in data and data["ai_consent"] is not None:
        user.ai_consent_at = utcnow() if data["ai_consent"] else None
        audit(db, user.id, "user.consent", "user", user.id, {"granted": data["ai_consent"]})
    if data.get("support_access_days") is not None:
        days = data["support_access_days"]
        user.support_access_until = utcnow() + timedelta(days=days) if days > 0 else None
        audit(db, user.id, "user.support_access", "user", user.id, {"days": days})
    audit(db, user.id, "user.profile_update", "user", user.id)
    db.commit()
    db.refresh(user)
    return user


@router.post("/password", status_code=204)
def change_password(body: ChangePasswordIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not verify_password(body.current_password, user.password_hash):
        raise AppError(400, "INVALID_CREDENTIALS", "Joriy parol noto'g'ri")
    problems = password_problems(body.new_password, user.email, (user.first_name, user.last_name))
    if problems:
        raise AppError(422, "WEAK_PASSWORD", problems[0])
    user.password_hash = hash_password(body.new_password)
    audit(db, user.id, "user.password_change", "user", user.id)
    db.commit()
    return Response(status_code=204)


def _results(db: Session, user: User) -> list[CompetencyResult]:
    return db.scalars(select(CompetencyResult).where(CompetencyResult.user_id == user.id)
                      .order_by(CompetencyResult.created_at)).all()


@router.get("/dashboard")
def dashboard(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    projects = db.scalar(select(func.count()).select_from(Project)
                         .where(Project.owner_id == user.id, Project.deleted_at.is_(None))) or 0
    done = db.scalar(select(func.count()).select_from(DefenseSession)
                     .where(DefenseSession.user_id == user.id, DefenseSession.status == SessionStatus.EVALUATED)) or 0
    ongoing = db.scalars(select(DefenseSession).where(
        DefenseSession.user_id == user.id,
        DefenseSession.status.in_([SessionStatus.CREATED, SessionStatus.IN_PROGRESS, SessionStatus.COMPLETED,
                                   SessionStatus.EVALUATING, SessionStatus.FAILED]))
        .order_by(DefenseSession.created_at.desc())).first()
    results = _results(db, user)
    last = results[-1] if results else None
    recs = []
    if last:
        recs = (last.summary_json.get("weaknesses") or [])[:3]
    activity = history_items(db, user, 5, 0)
    ongoing_view = None
    if ongoing:
        p = db.get(Project, ongoing.project_id)
        answered = db.scalar(select(func.count()).select_from(DefenseAnswer).join(DefenseQuestion)
                             .where(DefenseQuestion.session_id == ongoing.id)) or 0
        ongoing_view = {"id": str(ongoing.id), "status": ongoing.status.value, "mode": ongoing.mode.value,
                        "project_title": p.title if p else None, "answered": answered,
                        "question_limit": ongoing.question_limit}
    return {
        "first_name": user.first_name, "projects_count": projects, "completed_defenses": done,
        "ongoing_defense": ongoing_view,
        "latest_result": None if last is None else {
            "session_id": str(last.session_id), "total_score": last.total_score,
            "max_applicable_score": last.max_applicable_score, "level": last.level, "coverage": last.coverage,
            "percent": last.summary_json.get("percent"), "created_at": last.created_at.isoformat()},
        "recommendations": recs, "recent_activity": activity, "ai_consent": user.ai_consent_at is not None,
    }


@router.get("/competencies")
def competencies(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    results = _results(db, user)
    if not results:
        return {"latest": None, "by_criterion": {}}
    last = results[-1]
    by_crit: dict[str, list] = {}
    for r in results:
        for c in r.criteria_json:
            by_crit.setdefault(c["code"], []).append({"session_id": str(r.session_id), "percent": c["percent"],
                                                      "assessed": c["assessed"], "date": r.created_at.isoformat()})
    # K6 is assessed only in practice re-attempts.
    k6 = db.execute(select(PracticeAttempt.evaluation_json, PracticeAttempt.created_at).where(
        PracticeAttempt.user_id == user.id, PracticeAttempt.status == "evaluated")
        .order_by(PracticeAttempt.created_at)).all()
    by_crit["K6"] = [{"percent": round(100 * e["reflection"]["score"] / e["reflection"]["max_score"], 1),
                      "assessed": True, "date": d.isoformat()}
                     for e, d in k6 if e.get("reflection", {}).get("assessed")]
    return {"latest": {"session_id": str(last.session_id), "rubric_version": last.rubric_version,
                       "criteria": last.criteria_json, "total_score": last.total_score,
                       "max_applicable_score": last.max_applicable_score, "coverage": last.coverage,
                       "level": last.level, "readiness": last.readiness_json},
            "by_criterion": by_crit}


@router.get("/progress")
def progress(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    results = _results(db, user)
    points = []
    for r in results:
        s = db.get(DefenseSession, r.session_id)
        points.append({"session_id": str(r.session_id), "date": r.created_at.isoformat(),
                       "mode": s.mode.value if s else None, "percent": r.summary_json.get("percent"),
                       "total_score": r.total_score, "max_applicable_score": r.max_applicable_score,
                       "coverage": r.coverage, "level": r.level, "rubric_version": r.rubric_version,
                       "readiness_percent": (r.readiness_json or {}).get("percent")})
    practice = db.scalars(select(PracticeAttempt).where(PracticeAttempt.user_id == user.id,
                                                        PracticeAttempt.status == "evaluated")
                          .order_by(PracticeAttempt.created_at)).all()
    deltas = []
    for a in practice:
        row = next((c for c in a.evaluation_json.get("score_comparison", []) if c["code"] == a.target_competency), None)
        if row:
            deltas.append({"attempt_id": str(a.id), "competency": a.target_competency, "before": row["before"],
                           "after": row["after"], "delta": row.get("delta"), "date": a.created_at.isoformat()})
    return {"sessions": points, "practice": deltas}


def history_items(db: Session, user: User, limit: int, offset: int) -> list[dict]:
    rows = db.scalars(select(AuditLog).where(AuditLog.actor_id == user.id, AuditLog.action.in_(list(ACTIVITY_LABELS)),
                                             AuditLog.action != "user.login")
                      .order_by(AuditLog.created_at.desc()).offset(offset).limit(limit)).all()
    return [{"id": str(r.id), "action": r.action, "label": ACTIVITY_LABELS.get(r.action, r.action),
             "resource_type": r.resource_type, "resource_id": r.resource_id, "created_at": r.created_at.isoformat()}
            for r in rows]


@router.get("/history")
def history(page: Page = Depends(), user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    total = db.scalar(select(func.count()).select_from(AuditLog).where(
        AuditLog.actor_id == user.id, AuditLog.action.in_(list(ACTIVITY_LABELS)), AuditLog.action != "user.login")) or 0
    return page.wrap(history_items(db, user, page.page_size, page.offset), total)


@router.get("/export")
def export_data(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Personal data export (JSON) — everything stored about the user."""
    projects = db.scalars(select(Project).where(Project.owner_id == user.id)).all()
    out_projects = []
    for p in projects:
        analyses = db.scalars(select(ProjectAnalysis).where(ProjectAnalysis.project_id == p.id)).all()
        sessions = db.scalars(select(DefenseSession).where(DefenseSession.project_id == p.id)).all()
        out_projects.append({
            "id": str(p.id), "title": p.title, "category": p.category.value, "description": p.description,
            "problem": p.problem, "objective": p.objective, "target_users": p.target_users, "features": p.features,
            "technologies": p.technologies, "innovation": p.innovation, "expected_results": p.expected_results,
            "future_plans": p.future_plans, "created_at": p.created_at.isoformat(),
            "deleted_at": p.deleted_at.isoformat() if p.deleted_at else None,
            "files": [{"filename": f.original_filename, "size": f.file_size, "extracted_text": f.extracted_text}
                      for f in p.files],
            "analyses": [{"created_at": a.created_at.isoformat(), "status": a.status.value, "result": a.result_json}
                         for a in analyses],
            "defenses": [{
                "id": str(s.id), "mode": s.mode.value, "status": s.status.value, "rubric_version": s.rubric_version,
                "questions": [{"question": q.question_text, "answer": q.answer.answer_text if q.answer else None,
                               "evaluation": q.answer.evaluation.result_json if q.answer and q.answer.evaluation else None}
                              for q in s.questions]} for s in sessions],
        })
    results = _results(db, user)
    plans = db.scalars(select(ImprovementPlan).where(ImprovementPlan.user_id == user.id)).all()
    attempts = db.scalars(select(PracticeAttempt).where(PracticeAttempt.user_id == user.id)).all()
    audit(db, user.id, "user.export", "user", user.id)
    db.commit()
    return {
        "exported_at": utcnow().isoformat(),
        "user": UserOut.model_validate(user).model_dump(mode="json"),
        "projects": out_projects,
        "competency_results": [{"session_id": str(r.session_id), "total_score": r.total_score,
                                "max_applicable_score": r.max_applicable_score, "level": r.level,
                                "criteria": r.criteria_json, "summary": r.summary_json} for r in results],
        "improvement_plans": [{"id": str(p.id), "recommendations": p.recommendations_json} for p in plans],
        "practice_attempts": [{"revised_answer": a.revised_answer, "evaluation": a.evaluation_json} for a in attempts],
    }


@router.delete("", status_code=204)
def delete_account(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Permanently delete the account, its files (storage) and all related records."""
    storage = get_storage()
    for p in db.scalars(select(Project).where(Project.owner_id == user.id)).all():
        for f in p.files:
            try:
                storage.delete(f.storage_key)
            except Exception:  # noqa: BLE001
                pass
    db.execute(update(RefreshToken).where(RefreshToken.user_id == user.id).values(revoked_at=utcnow()))
    audit(db, None, "user.delete", "user", user.id)
    db.delete(user)
    db.commit()
    return Response(status_code=204)
