import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import (
    IdempotencyKey, Page, ai_rate_limit, audit, get_current_user, idem_get, idem_save, owned_session,
    require_ai_consent,
)
from app.core.database import get_db
from app.core.errors import AppError, conflict, not_found
from app.models import AIJob, ImprovementPlan, PracticeAttempt, Project, SessionStatus, User
from app.schemas import PracticeAttemptIn, PracticePlanCreate
from app.services import jobs
from app.services.evaluation.rubric import get_rubric

router = APIRouter(tags=["Communication Training"])


def _owned_plan(db: Session, plan_id: uuid.UUID, user: User) -> ImprovementPlan:
    plan = db.get(ImprovementPlan, plan_id)
    if plan is None or plan.user_id != user.id:
        raise not_found("Mashq rejasi")
    return plan


def attempt_view(db: Session, a: PracticeAttempt) -> dict:
    job = jobs.active_job(db, a.id, ("practice_attempt",))
    return {"id": str(a.id), "exercise_index": a.exercise_index, "target_competency": a.target_competency,
            "original_answer_id": str(a.original_answer_id), "revised_answer": a.revised_answer,
            "status": a.status, "evaluation": a.evaluation_json, "created_at": a.created_at.isoformat(),
            "job": jobs.job_view(job)}


def plan_view(db: Session, plan: ImprovementPlan) -> dict:
    project = db.get(Project, plan.project_id)
    rubric = get_rubric(plan.recommendations_json.get("rubric_version", "1.0"))
    exercises = []
    for i, ex in enumerate(plan.recommendations_json.get("exercises", [])):
        crit = rubric.criterion(ex["competency"])
        exercises.append({**ex, "index": i, "competency_title": crit.title})
    attempts = db.scalars(select(PracticeAttempt).where(PracticeAttempt.plan_id == plan.id)
                          .order_by(PracticeAttempt.created_at)).all()
    return {"id": str(plan.id), "session_id": str(plan.session_id), "project_id": str(plan.project_id),
            "project_title": project.title if project else None, "target_competencies": plan.target_competencies,
            "status": plan.status, "exercises": exercises, "attempts": [attempt_view(db, a) for a in attempts],
            "created_at": plan.created_at.isoformat()}


@router.post("/practice-plans", status_code=200)
def create_plan(body: PracticePlanCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Plans are generated during final evaluation (adaptive step); this returns the plan for a session."""
    s = owned_session(db, body.session_id, user)
    if s.status != SessionStatus.EVALUATED:
        raise conflict("NOT_EVALUATED", "Mashq rejasi himoya baholangandan so'ng yaratiladi")
    plan = db.scalars(select(ImprovementPlan).where(ImprovementPlan.session_id == s.id)).first()
    if plan is None:
        raise AppError(404, "NOT_FOUND", "Bu sessiya uchun mashq rejasi topilmadi")
    return plan_view(db, plan)


@router.get("/practice-plans")
def list_plans(page: Page = Depends(), user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    stmt = select(ImprovementPlan).where(ImprovementPlan.user_id == user.id)
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = db.scalars(stmt.order_by(ImprovementPlan.created_at.desc()).offset(page.offset).limit(page.page_size)).all()
    return page.wrap([plan_view(db, p) for p in rows], total)


@router.get("/practice-plans/{plan_id}")
def get_plan(plan_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return plan_view(db, _owned_plan(db, plan_id, user))


@router.post("/practice-plans/{plan_id}/attempts", status_code=202, dependencies=[Depends(ai_rate_limit)])
def create_attempt(plan_id: uuid.UUID, body: PracticeAttemptIn, idem_key: str | None = IdempotencyKey,
                   user: User = Depends(require_ai_consent), db: Session = Depends(get_db)):
    endpoint = f"attempt:{plan_id}"
    prev = idem_get(db, user, idem_key, endpoint)
    if prev:
        return prev.response_json
    plan = _owned_plan(db, plan_id, user)
    exercises = plan.recommendations_json.get("exercises", [])
    if body.exercise_index >= len(exercises):
        raise AppError(422, "VALIDATION_ERROR", "Mashq raqami noto'g'ri")
    pending = db.scalars(select(PracticeAttempt).where(PracticeAttempt.plan_id == plan.id,
                                                       PracticeAttempt.status == "pending")).first()
    if pending is not None and jobs.active_job(db, pending.id, ("practice_attempt",)):
        raise conflict("AI_BUSY", "Oldingi urinish hali baholanmoqda")
    ex = exercises[body.exercise_index]
    attempt = PracticeAttempt(plan_id=plan.id, user_id=user.id, exercise_index=body.exercise_index,
                              target_competency=ex["competency"], original_answer_id=uuid.UUID(ex["original_answer_id"]),
                              revised_answer=body.revised_answer, status="pending")
    db.add(attempt)
    db.flush()
    job = jobs.create_job(db, user_id=user.id, kind="practice_attempt", resource_type="practice_attempt",
                          resource_id=attempt.id)
    out = attempt_view(db, attempt)
    idem_save(db, user, idem_key, endpoint, 202, out)
    audit(db, user.id, "practice.attempt", "practice_attempt", attempt.id)
    db.commit()
    jobs.dispatch(job.id)
    db.expire_all()
    db.refresh(attempt)
    return attempt_view(db, attempt)


@router.post("/practice-attempts/{attempt_id}/retry", status_code=202, dependencies=[Depends(ai_rate_limit)])
def retry_attempt(attempt_id: uuid.UUID, user: User = Depends(require_ai_consent), db: Session = Depends(get_db)):
    a = db.get(PracticeAttempt, attempt_id)
    if a is None or a.user_id != user.id:
        raise not_found("Urinish")
    if a.status == "evaluated":
        return attempt_view(db, a)
    job = jobs.active_job(db, a.id, ("practice_attempt",))
    if job is None:
        a.status = "pending"
        a.evaluation_json = None
        job = jobs.create_job(db, user_id=user.id, kind="practice_attempt", resource_type="practice_attempt",
                              resource_id=a.id)
        db.commit()
        jobs.dispatch(job.id)
        db.expire_all()
        db.refresh(a)
    return attempt_view(db, a)


@router.get("/practice-plans/{plan_id}/progress")
def plan_progress(plan_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    plan = _owned_plan(db, plan_id, user)
    view = plan_view(db, plan)
    rows = []
    for ex in view["exercises"]:
        tries = [a for a in view["attempts"] if a["exercise_index"] == ex["index"] and a["status"] == "evaluated"]
        latest = tries[-1] if tries else None
        target = ex["competency"]
        cmp = next((c for c in (latest["evaluation"]["score_comparison"] if latest else []) if c["code"] == target), None)
        rows.append({
            "exercise_index": ex["index"], "competency": target, "competency_title": ex["competency_title"],
            "attempts": len(tries),
            "before": cmp["before"] if cmp else None, "after": cmp["after"] if cmp else None,
            "delta": cmp.get("delta") if cmp else None,
            "reflection": latest["evaluation"]["reflection"] if latest else None,
            "comparison": latest["evaluation"]["comparison"] if latest else None,
        })
    return {"plan_id": str(plan.id), "status": plan.status, "rows": rows,
            "note": "Avvalgi va yangi javoblar bir xil rubrika versiyasi asosida solishtirildi."}


@router.get("/jobs/{job_id}", tags=["Jobs"])
def get_job(job_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    job = db.get(AIJob, job_id)
    if job is None or job.user_id != user.id:
        raise not_found("Vazifa")
    return jobs.job_view(job)
