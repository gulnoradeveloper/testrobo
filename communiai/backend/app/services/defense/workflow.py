"""Virtual defense workflow: question generation, per-answer evaluation, final assessment, practice.

State machine (enforced here and in the API layer):
CREATED -> IN_PROGRESS -> COMPLETED -> EVALUATING -> EVALUATED
                   \\-> CANCELLED              \\-> FAILED -> EVALUATING (retry)
"""
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError, conflict
from app.models import (
    AIJob, AnswerEvaluation, CompetencyResult, DefenseAnswer, DefenseQuestion, DefenseSession, ImprovementPlan,
    PracticeAttempt, Project, SessionStatus, utcnow,
)
from app.services import jobs
from app.services.ai import services as ai
from app.services.evaluation.rubric import aggregate, aggregate_readiness, get_rubric, weakest_criteria

SESSION_JOB_KINDS = ("defense_question", "defense_answer", "defense_final")

ALLOWED_TRANSITIONS = {
    SessionStatus.CREATED: {SessionStatus.IN_PROGRESS, SessionStatus.CANCELLED},
    SessionStatus.IN_PROGRESS: {SessionStatus.COMPLETED, SessionStatus.CANCELLED},
    SessionStatus.COMPLETED: {SessionStatus.EVALUATING},
    SessionStatus.EVALUATING: {SessionStatus.EVALUATED, SessionStatus.FAILED},
    SessionStatus.FAILED: {SessionStatus.EVALUATING},
    SessionStatus.EVALUATED: set(),
    SessionStatus.CANCELLED: set(),
}


def transition(session: DefenseSession, new: SessionStatus) -> None:
    if new not in ALLOWED_TRANSITIONS[session.status]:
        raise conflict("INVALID_STATE", f"Sessiya holatini {session.status.value} dan {new.value} ga o'zgartirib bo'lmaydi")
    session.status = new
    now = utcnow()
    if new == SessionStatus.IN_PROGRESS:
        session.started_at = now
    elif new == SessionStatus.COMPLETED:
        session.completed_at = now
    elif new == SessionStatus.EVALUATED:
        session.evaluated_at = now


def _project(db: Session, session: DefenseSession) -> Project:
    project = db.get(Project, session.project_id)
    if project is None or project.deleted_at is not None:
        raise AppError(409, "PROJECT_UNAVAILABLE", "Loyiha o'chirilgan")
    return project


def _history(session: DefenseSession) -> list[dict]:
    hist = []
    for q in session.questions:
        item = {"seq": q.sequence_number, "type": q.question_type, "focus": q.focus_area, "question": q.question_text,
                "answer": q.answer.answer_text if q.answer else None}
        if q.answer and q.answer.evaluation:
            ev = q.answer.evaluation.result_json
            item["needs_follow_up"] = ev.get("needs_follow_up")
            item["follow_up_reason"] = ev.get("follow_up_reason")
        hist.append(item)
    return hist


def session_progress(session: DefenseSession) -> dict:
    qs = session.questions
    answered = sum(1 for q in qs if q.answer is not None)
    evaluated = sum(1 for q in qs if q.answer is not None and q.answer.evaluation is not None)
    current = qs[-1] if qs and qs[-1].answer is None else None
    return {"asked": len(qs), "answered": answered, "evaluated": evaluated, "current": current,
            "all_answered": answered >= session.question_limit,
            "ready_to_complete": answered >= session.question_limit and evaluated >= answered}


def missing_work(session: DefenseSession) -> str | None:
    """Which job kind would move an IN_PROGRESS session forward, if any."""
    if session.status != SessionStatus.IN_PROGRESS:
        return None
    p = session_progress(session)
    if p["evaluated"] < p["answered"]:
        return "defense_answer"
    if p["current"] is None and p["asked"] < session.question_limit:
        return "defense_question"
    return None


def enqueue_session_job(db: Session, session: DefenseSession, kind: str, payload: dict | None = None) -> AIJob:
    existing = jobs.active_job(db, session.id, SESSION_JOB_KINDS)
    if existing:
        return existing
    return jobs.create_job(db, user_id=session.user_id, kind=kind, resource_type="defense_session",
                           resource_id=session.id, payload=payload)


# ------------------------------------------------------------------ job handlers
def _generate_next_question(db: Session, session: DefenseSession) -> None:
    p = session_progress(session)
    if p["current"] is not None or p["asked"] >= session.question_limit:
        return
    project = _project(db, session)
    q = ai.generate_question(project, session.mode.value, session.question_limit, _history(session), session.user_id)
    db.add(DefenseQuestion(session_id=session.id, sequence_number=p["asked"] + 1, question_text=q.question,
                           question_type=q.question_type, project_reference=q.project_reference,
                           focus_area=q.focus_area[:120]))
    db.flush()
    db.refresh(session)


def handle_question(db: Session, job: AIJob) -> None:
    session = db.get(DefenseSession, job.resource_id)
    if session.status != SessionStatus.IN_PROGRESS:
        return
    _generate_next_question(db, session)


def handle_answer(db: Session, job: AIJob) -> None:
    session = db.get(DefenseSession, job.resource_id)
    if session.status != SessionStatus.IN_PROGRESS:
        return
    project = _project(db, session)
    rubric = get_rubric(session.rubric_version)
    for q in session.questions:
        if q.answer is not None and q.answer.evaluation is None:
            result = ai.evaluate_answer(project, session.mode.value, rubric, q.question_text, q.answer.answer_text,
                                        session.user_id)
            result["question_id"] = str(q.id)
            result["answer_id"] = str(q.answer.id)
            db.add(AnswerEvaluation(answer_id=q.answer.id, rubric_version=rubric.version,
                                    ai_model=_model_name(), result_json=result))
            db.commit()  # keep each evaluation even if a later step fails
            db.refresh(session)
    _generate_next_question(db, session)


def handle_final(db: Session, job: AIJob) -> None:
    session = db.get(DefenseSession, job.resource_id)
    if session.status != SessionStatus.EVALUATING:
        return
    project = _project(db, session)
    rubric = get_rubric(session.rubric_version)
    answered = [q for q in session.questions if q.answer is not None]
    # Evaluate any answer that is still missing an evaluation (e.g. after an AI outage).
    for q in answered:
        if q.answer.evaluation is None:
            result = ai.evaluate_answer(project, session.mode.value, rubric, q.question_text, q.answer.answer_text,
                                        session.user_id)
            result.update(question_id=str(q.id), answer_id=str(q.answer.id))
            db.add(AnswerEvaluation(answer_id=q.answer.id, rubric_version=rubric.version, ai_model=_model_name(),
                                    result_json=result))
            db.commit()
            db.refresh(session)
    evals = [q.answer.evaluation.result_json for q in answered]
    aggregated = aggregate(rubric, [e["criteria"] for e in evals])
    readiness = aggregate_readiness([e["readiness"] for e in evals])
    targets = weakest_criteria(aggregated, 2)
    qa = [{"seq": q.sequence_number, "question": q.question_text, "answer": q.answer.answer_text,
           "eval_summary": {c["code"]: c["score"] for c in q.answer.evaluation.result_json["criteria"]}}
          for q in answered]
    coach = ai.final_coach(project, session.mode.value, rubric, qa, aggregated, targets, session.user_id)

    limitations = [
        "Natijalar matnli javoblar asosida AI tomonidan berilgan dastlabki baho hisoblanadi.",
        "Ushbu ballar va darajalar validatsiyadan o'tgan pedagogik o'lchov emas; ekspert bahosi va pilot sinov talab etiladi.",
        "Nutq intonatsiyasi, ovoz ravonligi, jamoaviy hamkorlik va haqiqiy muzokara samaradorligi matn asosida baholanmaydi.",
    ] + coach["limitations"]
    db.add(CompetencyResult(
        session_id=session.id, user_id=session.user_id, rubric_version=rubric.version,
        total_score=aggregated["total_score"], max_applicable_score=aggregated["max_applicable_score"],
        coverage=aggregated["coverage"], level=aggregated["level"], criteria_json=aggregated["criteria"],
        readiness_json=readiness,
        summary_json={"percent": aggregated["percent"], "overall_summary": coach["overall_summary"],
                      "strengths": coach["strengths"], "weaknesses": coach["weaknesses"],
                      "detailed_analysis": coach["detailed_analysis"],
                      "project_recommendations": coach["project_recommendations"], "limitations": limitations},
    ))
    seq_to_answer = {q.sequence_number: q.answer for q in answered}
    exercises = []
    for ex in coach["exercises"]:
        ans = seq_to_answer.get(ex["question_sequence"]) or answered[-1].answer
        exercises.append({**ex, "original_answer_id": str(ans.id), "question_text": ans.question.question_text,
                          "original_answer": ans.answer_text})
    db.add(ImprovementPlan(user_id=session.user_id, project_id=session.project_id, session_id=session.id,
                           target_competencies=targets,
                           recommendations_json={"exercises": exercises, "rubric_version": rubric.version}))
    transition(session, SessionStatus.EVALUATED)
    session.failure_reason = None


def on_final_failure(db: Session, job: AIJob, code: str, message: str) -> None:
    session = db.get(DefenseSession, job.resource_id)
    if session and session.status == SessionStatus.EVALUATING:
        session.status = SessionStatus.FAILED
        session.failure_reason = message


def handle_practice(db: Session, job: AIJob) -> None:
    attempt = db.get(PracticeAttempt, job.resource_id)
    plan = db.get(ImprovementPlan, attempt.plan_id)
    session = db.get(DefenseSession, plan.session_id)
    project = _project(db, session)
    rubric = get_rubric(plan.recommendations_json.get("rubric_version", session.rubric_version))
    exercise = plan.recommendations_json["exercises"][attempt.exercise_index]
    original = db.get(DefenseAnswer, attempt.original_answer_id)
    original_eval = original.evaluation.result_json if original.evaluation else {}
    result = ai.evaluate_practice(
        project, session.mode.value, rubric, original.question.question_text, original.answer_text,
        original_eval.get("feedback", {}), {k: exercise[k] for k in ("competency", "title", "task", "success_criteria")},
        attempt.revised_answer, attempt.user_id)
    before = {c["code"]: c for c in original_eval.get("criteria", [])}
    comparison_rows = []
    for c in result["criteria"]:
        b = before.get(c["code"], {})
        comparison_rows.append({
            "code": c["code"], "max_score": c["max_score"],
            "before": b.get("score") if b.get("assessed") else None,
            "after": c["score"] if c["assessed"] else None,
        })
        if comparison_rows[-1]["before"] is not None and comparison_rows[-1]["after"] is not None:
            comparison_rows[-1]["delta"] = round(comparison_rows[-1]["after"] - comparison_rows[-1]["before"], 1)
    result["score_comparison"] = comparison_rows
    attempt.evaluation_json = result
    attempt.status = "evaluated"
    _maybe_complete_plan(db, plan)


def _maybe_complete_plan(db: Session, plan: ImprovementPlan) -> None:
    n = len(plan.recommendations_json.get("exercises", []))
    done = set(db.scalars(select(PracticeAttempt.exercise_index).where(
        PracticeAttempt.plan_id == plan.id, PracticeAttempt.status == "evaluated")).all())
    if n and len(done | set()) >= n:
        plan.status = "completed"


def on_practice_failure(db: Session, job: AIJob, code: str, message: str) -> None:
    attempt = db.get(PracticeAttempt, job.resource_id)
    if attempt and attempt.status == "pending":
        attempt.status = "failed"
        attempt.evaluation_json = {"error_code": code, "error_message": message}


def _model_name() -> str:
    from app.services.ai.provider import get_provider
    return get_provider().model


def register_handlers() -> None:
    jobs.register("defense_question", handle_question)
    jobs.register("defense_answer", handle_answer)
    jobs.register("defense_final", handle_final, on_final_failure)
    jobs.register("practice_attempt", handle_practice, on_practice_failure)


def new_session_id() -> uuid.UUID:
    return uuid.uuid4()
