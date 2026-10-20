import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import (
    IdempotencyKey, Page, ai_rate_limit, audit, get_current_user, idem_get, idem_save, owned_project, owned_session,
    require_ai_consent,
)
from app.core.config import get_settings
from app.core.database import get_db
from app.core.errors import AppError, conflict
from app.models import (
    AIJob, CompetencyResult, DefenseAnswer, DefenseQuestion, DefenseSession, ImprovementPlan, SessionStatus, User,
)
from app.schemas import AnswerIn, DefenseCreate
from app.services import jobs
from app.services.defense import workflow as wf
from app.services.projects.context import has_minimum_data, snapshot_hash

router = APIRouter(prefix="/defenses", tags=["Defense"])

MODE_LABELS = {"hackathon": "Hakaton va tanlov", "client": "Buyurtmachi bilan suhbat",
               "academic": "Akademik loyiha himoyasi", "investor": "Investor oldida taqdimot"}


def question_view(q: DefenseQuestion, with_answer: bool = True) -> dict:
    data = {"id": str(q.id), "sequence_number": q.sequence_number, "question_text": q.question_text,
            "question_type": q.question_type, "focus_area": q.focus_area, "project_reference": q.project_reference,
            "created_at": q.created_at.isoformat()}
    if with_answer:
        a = q.answer
        data["answer"] = None if a is None else {
            "id": str(a.id), "answer_text": a.answer_text, "submitted_at": a.submitted_at.isoformat(),
            "evaluation": a.evaluation.result_json if a.evaluation else None,
        }
    return data


def session_view(db: Session, s: DefenseSession, full: bool = True) -> dict:
    p = wf.session_progress(s)
    job = jobs.active_job(db, s.id, wf.SESSION_JOB_KINDS)
    last_failed = None
    if job is None:
        last = db.scalars(select(AIJob).where(AIJob.resource_id == s.id).order_by(AIJob.created_at.desc())).first()
        if last is not None and last.status.value == "failed":
            last_failed = jobs.job_view(last)
    project = s.project_id
    data = {
        "id": str(s.id), "project_id": str(project), "mode": s.mode.value, "mode_label": MODE_LABELS[s.mode.value],
        "question_limit": s.question_limit, "status": s.status.value, "rubric_version": s.rubric_version,
        "failure_reason": s.failure_reason, "created_at": s.created_at.isoformat(),
        "started_at": s.started_at.isoformat() if s.started_at else None,
        "completed_at": s.completed_at.isoformat() if s.completed_at else None,
        "evaluated_at": s.evaluated_at.isoformat() if s.evaluated_at else None,
        "progress": {k: v for k, v in p.items() if k != "current"},
        "current_question": question_view(p["current"], with_answer=False) if p["current"] else None,
        "active_job": jobs.job_view(job), "last_failed_job": last_failed,
        "pending_work": wf.missing_work(s) if job is None else None,
    }
    if full:
        data["questions"] = [question_view(q) for q in s.questions]
    from app.models import Project
    proj = db.get(Project, s.project_id)
    data["project_title"] = proj.title if proj else None
    return data


def _dispatch_after_commit(db: Session, job: AIJob | None) -> None:
    if job is not None and job.status.value == "queued":
        db.commit()
        jobs.dispatch(job.id)
        db.expire_all()


@router.post("", status_code=201, dependencies=[Depends(ai_rate_limit)])
def create_defense(body: DefenseCreate, idem_key: str | None = IdempotencyKey,
                   user: User = Depends(require_ai_consent), db: Session = Depends(get_db)):
    prev = idem_get(db, user, idem_key, "defense:create")
    if prev:
        return prev.response_json
    project = owned_project(db, body.project_id, user)
    missing = has_minimum_data(project)
    if missing:
        raise AppError(422, "PROJECT_INCOMPLETE", "Himoya uchun loyiha ma'lumotlari yetarli emas", {"missing": missing})
    s = DefenseSession(project_id=project.id, user_id=user.id, mode=body.mode, question_limit=body.question_limit,
                       status=SessionStatus.CREATED, rubric_version=get_settings().RUBRIC_VERSION,
                       project_snapshot_hash=snapshot_hash(project))
    db.add(s)
    db.flush()
    db.refresh(s)
    view = session_view(db, s)
    idem_save(db, user, idem_key, "defense:create", 201, view)
    audit(db, user.id, "defense.create", "defense_session", s.id, {"mode": body.mode.value})
    db.commit()
    return view


@router.get("")
def list_defenses(page: Page = Depends(), status: SessionStatus | None = None, project_id: uuid.UUID | None = None,
                  user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    stmt = select(DefenseSession).where(DefenseSession.user_id == user.id)
    if status:
        stmt = stmt.where(DefenseSession.status == status)
    if project_id:
        stmt = stmt.where(DefenseSession.project_id == project_id)
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = db.scalars(stmt.order_by(DefenseSession.created_at.desc()).offset(page.offset).limit(page.page_size)).all()
    items = []
    for s in rows:
        v = session_view(db, s, full=False)
        r = db.scalars(select(CompetencyResult).where(CompetencyResult.session_id == s.id)).first()
        v["result"] = None if r is None else {"total_score": r.total_score, "max_applicable_score": r.max_applicable_score,
                                              "level": r.level, "coverage": r.coverage}
        items.append(v)
    return page.wrap(items, total)


@router.get("/{session_id}")
def get_defense(session_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return session_view(db, owned_session(db, session_id, user))


@router.post("/{session_id}/start", dependencies=[Depends(ai_rate_limit)])
def start_defense(session_id: uuid.UUID, user: User = Depends(require_ai_consent), db: Session = Depends(get_db)):
    """Start a CREATED session, or resume an IN_PROGRESS one (idempotent)."""
    s = owned_session(db, session_id, user)
    owned_project(db, s.project_id, user)
    if s.status == SessionStatus.CREATED:
        wf.transition(s, SessionStatus.IN_PROGRESS)
        audit(db, user.id, "defense.start", "defense_session", s.id)
    elif s.status != SessionStatus.IN_PROGRESS:
        raise conflict("INVALID_STATE", "Sessiyani faqat CREATED yoki IN_PROGRESS holatida boshlash/davom ettirish mumkin")
    job = None
    kind = wf.missing_work(s)
    if kind:
        job = wf.enqueue_session_job(db, s, kind)
    db.commit()
    _dispatch_after_commit(db, job)
    db.refresh(s)
    return session_view(db, s)


# Same behaviour under a clearer name for the client's "Qayta urinish" (retry) button.
router.add_api_route("/{session_id}/resume", start_defense, methods=["POST"], dependencies=[Depends(ai_rate_limit)])


@router.get("/{session_id}/current-question")
def current_question(session_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    s = owned_session(db, session_id, user)
    p = wf.session_progress(s)
    last_answered = next((q for q in reversed(s.questions) if q.answer is not None), None)
    view = session_view(db, s, full=False)
    return {
        "status": s.status.value,
        "question": question_view(p["current"], with_answer=False) if p["current"] else None,
        "progress": view["progress"], "question_limit": s.question_limit,
        "active_job": view["active_job"], "last_failed_job": view["last_failed_job"],
        "pending_work": view["pending_work"],
        "last_feedback": None if last_answered is None or last_answered.answer.evaluation is None else {
            "question_id": str(last_answered.id), "sequence_number": last_answered.sequence_number,
            "feedback": last_answered.answer.evaluation.result_json.get("feedback"),
        },
    }


@router.post("/{session_id}/answers", status_code=202, dependencies=[Depends(ai_rate_limit)])
def submit_answer(session_id: uuid.UUID, body: AnswerIn, idem_key: str | None = IdempotencyKey,
                  user: User = Depends(require_ai_consent), db: Session = Depends(get_db)):
    endpoint = f"answer:{session_id}"
    prev = idem_get(db, user, idem_key, endpoint)
    if prev:
        return prev.response_json
    s = owned_session(db, session_id, user)
    if s.status != SessionStatus.IN_PROGRESS:
        raise conflict("INVALID_STATE", "Javob faqat faol (IN_PROGRESS) sessiyada qabul qilinadi")
    q = next((x for x in s.questions if x.id == body.question_id), None)
    if q is None:
        raise AppError(404, "NOT_FOUND", "Savol topilmadi")
    if q.answer is not None:
        if q.answer.answer_text == body.answer_text:  # duplicate submit of the same answer
            return {"answer_id": str(q.answer.id), "question_id": str(q.id), "duplicate": True,
                    "job": jobs.job_view(jobs.active_job(db, s.id, wf.SESSION_JOB_KINDS))}
        raise conflict("ANSWER_LOCKED", "Bu savolga javob allaqachon yuborilgan va uni o'zgartirib bo'lmaydi")
    if s.questions[-1].id != q.id:
        raise conflict("NOT_CURRENT_QUESTION", "Faqat joriy savolga javob berish mumkin")
    ans = DefenseAnswer(question_id=q.id, user_id=user.id, answer_text=body.answer_text)
    db.add(ans)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise conflict("ANSWER_LOCKED", "Bu savolga javob allaqachon yuborilgan") from None
    db.refresh(s)
    job = wf.enqueue_session_job(db, s, "defense_answer")
    body_out = {"answer_id": str(ans.id), "question_id": str(q.id), "duplicate": False, "job": jobs.job_view(job)}
    idem_save(db, user, idem_key, endpoint, 202, body_out)
    db.commit()
    _dispatch_after_commit(db, job)
    db.refresh(job)
    body_out["job"] = jobs.job_view(job)
    return body_out


@router.post("/{session_id}/complete", status_code=202, dependencies=[Depends(ai_rate_limit)])
def complete_defense(session_id: uuid.UUID, user: User = Depends(require_ai_consent), db: Session = Depends(get_db)):
    s = owned_session(db, session_id, user)
    if s.status in (SessionStatus.EVALUATING, SessionStatus.EVALUATED):
        return session_view(db, s)  # idempotent
    if jobs.active_job(db, s.id, wf.SESSION_JOB_KINDS):
        raise conflict("AI_BUSY", "AI hali oxirgi javobni qayta ishlamoqda. Birozdan so'ng urinib ko'ring.")
    if s.status == SessionStatus.IN_PROGRESS:
        p = wf.session_progress(s)
        if not p["all_answered"]:
            raise conflict("NOT_ALL_ANSWERED", "Barcha savollarga javob berilmagan",
                           {"answered": p["answered"], "limit": s.question_limit})
        wf.transition(s, SessionStatus.COMPLETED)
        wf.transition(s, SessionStatus.EVALUATING)
    elif s.status in (SessionStatus.COMPLETED, SessionStatus.FAILED):
        wf.transition(s, SessionStatus.EVALUATING)
    else:
        raise conflict("INVALID_STATE", f"{s.status.value} holatidagi sessiyani yakunlab bo'lmaydi")
    s.failure_reason = None
    job = wf.enqueue_session_job(db, s, "defense_final")
    audit(db, user.id, "defense.complete", "defense_session", s.id)
    db.commit()
    _dispatch_after_commit(db, job)
    db.refresh(s)
    return session_view(db, s)


@router.post("/{session_id}/cancel")
def cancel_defense(session_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    s = owned_session(db, session_id, user)
    wf.transition(s, SessionStatus.CANCELLED)
    audit(db, user.id, "defense.cancel", "defense_session", s.id)
    db.commit()
    return session_view(db, s)


@router.get("/{session_id}/results")
def defense_results(session_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    s = owned_session(db, session_id, user)
    view = session_view(db, s)
    r = db.scalars(select(CompetencyResult).where(CompetencyResult.session_id == s.id)).first()
    plan = db.scalars(select(ImprovementPlan).where(ImprovementPlan.session_id == s.id)).first()
    view["result"] = None if r is None else {
        "rubric_version": r.rubric_version, "total_score": r.total_score, "max_applicable_score": r.max_applicable_score,
        "percent": r.summary_json.get("percent"), "coverage": r.coverage, "level": r.level,
        "criteria": r.criteria_json, "readiness": r.readiness_json, "summary": r.summary_json,
        "created_at": r.created_at.isoformat(),
        "disclaimer": "Ushbu ball va darajalar AI asosidagi dastlabki diagnostika bo'lib, validatsiyadan o'tgan "
                      "pedagogik o'lchov hisoblanmaydi.",
    }
    view["plan_id"] = str(plan.id) if plan else None
    return view
