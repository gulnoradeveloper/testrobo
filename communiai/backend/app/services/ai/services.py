"""The four AI services: project analysis, expert questions, communication evaluation, improvement coach.

Every service builds its own task-specific prompt, validates the structured output with Pydantic and
post-processes it so nothing unsupported by evidence reaches the user as a score or a fact.
"""
import json
import uuid

from app.models import Project
from app.services.ai import prompts as P
from app.services.ai.provider import call_structured
from app.services.ai.schemas import (
    ANALYSIS_DIMENSIONS, AnswerEvaluationOut, FinalCoachOut, PracticeEvaluationOut, ProjectAnalysisOut,
    QuestionOut,
)
from app.services.evaluation.rubric import PER_ANSWER_CODES, Rubric, clamp_score
from app.services.projects.context import corpus, documents_text, fields_text

MAX_ANSWER_CHARS = 6000


def _project_block(project: Project) -> str:
    docs = documents_text(project)
    return (
        "PROJECT DATA (entered by the student):\n" + P.untrusted("project_fields", fields_text(project), 15_000)
        + "\n\nUPLOADED DOCUMENTS (extracted text):\n"
        + (P.untrusted("documents", docs, 60_000) if docs else "Hujjat yuklanmagan yoki matn ajratilmagan.")
    )


def _rubric_block(rubric: Rubric) -> str:
    rows = [f"- {c.code} (max {c.max_score}): {c.title}. {c.description}"
            for c in rubric.criteria if c.code in PER_ANSWER_CODES]
    return f"RUBRIC version {rubric.version}:\n" + "\n".join(rows)


# --------------------------------------------------------------------------- 13.1 Project analysis
def analyze_project(project: Project, user_id: uuid.UUID) -> dict:
    system = P.PROJECT_ANALYSIS_SYSTEM.replace("{dimensions}", "; ".join(ANALYSIS_DIMENSIONS))
    user = _project_block(project) + "\n\nProduce the project expertise report as JSON."
    out = call_structured("project_analysis", system=system, user_content=user, schema=ProjectAnalysisOut,
                          user_id=user_id, max_tokens=16000)
    result = out.model_dump()
    # Drop strengths whose evidence cannot be found in the project data.
    source = corpus(project)
    verified, dropped = [], 0
    for s in result["strengths"]:
        if P.quote_supported(s["evidence_quote"], source):
            verified.append(s)
        else:
            dropped += 1
    result["strengths"] = verified
    result["verification"] = {
        "unsupported_strengths_removed": dropped,
        "note": ("Ba'zi kuchli jihatlar loyiha ma'lumotlarida dalil topilmagani uchun olib tashlandi."
                 if dropped else ""),
    }
    return result


# --------------------------------------------------------------------------- 13.2 Expert questions
def generate_question(project: Project, mode: str, question_limit: int, history: list[dict],
                      user_id: uuid.UUID) -> QuestionOut:
    role, focus = P.MODE_BRIEFS[mode]
    hist_lines = []
    for h in history:
        hist_lines.append(f"Q{h['seq']} [{h['type']}; focus: {h.get('focus') or '-'}]: {h['question']}")
        hist_lines.append("A: " + P.untrusted(f"answer_{h['seq']}", h.get("answer") or "(javob berilmagan)", 4000))
        if h.get("needs_follow_up") is not None:
            hist_lines.append(f"Evaluator note: needs_follow_up={h['needs_follow_up']}; "
                              f"reason={h.get('follow_up_reason') or '-'}")
    next_seq = len(history) + 1
    user = (
        f"DEFENSE MODE: {mode} — you play the role: {role}. Focus areas: {focus}.\n"
        f"This is question {next_seq} of {question_limit}.\n\n"
        + _project_block(project)
        + "\n\nPREVIOUS QUESTIONS AND ANSWERS:\n" + ("\n".join(hist_lines) if hist_lines else "(none yet)")
        + "\n\nGenerate the next question as JSON."
    )

    asked = {P.normalize(h["question"]) for h in history}

    def _validate(q: QuestionOut):
        from app.services.ai.provider import AIInvalidOutputError
        if P.normalize(q.question) in asked:
            raise AIInvalidOutputError("repeated question")

    return call_structured("expert_question", system=P.EXPERT_QUESTION_SYSTEM, user_content=user,
                           schema=QuestionOut, user_id=user_id, max_tokens=4000, validator=_validate)


# --------------------------------------------------------------------------- 13.3 Communication evaluation
def _postprocess_criteria(criteria: list[dict], rubric: Rubric, answer_text: str) -> tuple[list[dict], list[str]]:
    out, notes = [], []
    for c in sorted(criteria, key=lambda x: x["code"]):
        crit = rubric.criterion(c["code"])
        item = {
            "code": c["code"], "max_score": crit.max_score, "assessed": bool(c["assessed"]),
            "score": clamp_score(c["score"], crit.max_score) if c["assessed"] else None,
            "evidence": c["evidence_quote"], "feedback": c["feedback"], "recommendation": c["recommendation"],
            "confidence_limit": c["confidence_limit"],
        }
        if item["assessed"] and not P.quote_supported(item["evidence"], answer_text):
            item.update(assessed=False, score=None,
                        confidence_limit="Ball olib tashlandi: keltirilgan dalil javob matnida topilmadi.")
            notes.append(f"{c['code']}: dalil javob matnida topilmagani uchun baholanmadi.")
        if c["score"] > crit.max_score:
            notes.append(f"{c['code']}: AI bergan ball maksimaldan oshgani uchun cheklandi.")
        out.append(item)
    return out, notes


def evaluate_answer(project: Project, mode: str, rubric: Rubric, question: str, answer_text: str,
                    user_id: uuid.UUID) -> dict:
    role, _ = P.MODE_BRIEFS[mode]
    user = (
        _rubric_block(rubric) + f"\n\nAUDIENCE (defense mode): {mode} — {role}.\n\n" + _project_block(project)
        + f"\n\nQUESTION:\n{question}\n\nSTUDENT ANSWER:\n" + P.untrusted("student_answer", answer_text, MAX_ANSWER_CHARS)
        + "\n\nEvaluate the answer as JSON."
    )
    out = call_structured("communication_evaluation", system=P.COMMUNICATION_EVAL_SYSTEM, user_content=user,
                          schema=AnswerEvaluationOut, user_id=user_id, max_tokens=8000)
    data = out.model_dump()
    criteria, notes = _postprocess_criteria(data["criteria"], rubric, answer_text)
    readiness = data["content_readiness"]
    return {
        "evaluation_status": "completed",
        "rubric_version": rubric.version,
        "criteria": criteria,
        "readiness": {"assessed": readiness["assessed"], "score": max(0, min(10, readiness["score"])),
                      "comment": readiness["comment"]},
        "technical_note": data["technical_note"],
        "feedback": data["feedback"],
        "limitations": ["Baholash faqat matnli javob asosida bajarildi."] + data["limitations"] + notes,
        "needs_follow_up": data["needs_follow_up"],
        "follow_up_reason": data["follow_up_reason"],
    }


# --------------------------------------------------------------------------- 13.4 Improvement coach
def final_coach(project: Project, mode: str, rubric: Rubric, qa: list[dict], aggregated: dict,
                targets: list[str], user_id: uuid.UUID) -> dict:
    qa_lines = []
    for item in qa:
        qa_lines.append(f"Q{item['seq']}: {item['question']}")
        qa_lines.append("A: " + P.untrusted(f"answer_{item['seq']}", item["answer"], 4000))
        qa_lines.append("Per-answer evaluation summary: " + json.dumps(item.get("eval_summary", {}), ensure_ascii=False))
    agg_view = [{k: c[k] for k in ("code", "title", "score", "max_score", "assessed")} for c in aggregated["criteria"]]
    user = (
        _rubric_block(rubric) + f"\n\nDEFENSE MODE: {mode}.\n\n" + _project_block(project)
        + "\n\nDEFENSE TRANSCRIPT:\n" + "\n".join(qa_lines)
        + "\n\nAGGREGATED CRITERIA (computed by the backend, do not recompute):\n"
        + json.dumps(agg_view, ensure_ascii=False)
        + f"\n\nTARGET COMPETENCIES FOR EXERCISES (weakest): {', '.join(targets) if targets else 'none'}"
        + f"\nValid question_sequence values: 1..{len(qa)}.\n\nProduce the final coaching report as JSON."
    )

    def _validate(o: FinalCoachOut):
        from app.services.ai.provider import AIInvalidOutputError
        got = sorted({e.competency for e in o.exercises})
        if targets and got != sorted(targets):
            raise AIInvalidOutputError("exercises must match target competencies")
        if any(e.question_sequence > len(qa) for e in o.exercises):
            raise AIInvalidOutputError("invalid question_sequence")

    out = call_structured("improvement_coach", system=P.IMPROVEMENT_COACH_SYSTEM, user_content=user,
                          schema=FinalCoachOut, user_id=user_id, max_tokens=16000, validator=_validate)
    return out.model_dump()


def evaluate_practice(project: Project, mode: str, rubric: Rubric, question: str, original_answer: str,
                      original_feedback: dict, exercise: dict, revised: str, user_id: uuid.UUID) -> dict:
    user = (
        _rubric_block(rubric) + f"\n\nDEFENSE MODE: {mode}.\n\n" + _project_block(project)
        + f"\n\nQUESTION:\n{question}\n\nORIGINAL ANSWER:\n" + P.untrusted("original_answer", original_answer, MAX_ANSWER_CHARS)
        + "\n\nFEEDBACK GIVEN EARLIER:\n" + json.dumps(original_feedback, ensure_ascii=False)
        + "\n\nEXERCISE:\n" + json.dumps(exercise, ensure_ascii=False)
        + "\n\nREVISED ANSWER:\n" + P.untrusted("revised_answer", revised, MAX_ANSWER_CHARS)
        + "\n\nEvaluate the revised answer as JSON."
    )
    out = call_structured("practice_evaluation", system=P.PRACTICE_EVAL_SYSTEM, user_content=user,
                          schema=PracticeEvaluationOut, user_id=user_id, max_tokens=8000)
    data = out.model_dump()
    criteria, notes = _postprocess_criteria(data["criteria"], rubric, revised)
    refl = data["reflection"]
    k6_max = rubric.criterion("K6").max_score
    k6 = {"code": "K6", "max_score": k6_max, "assessed": bool(refl["assessed"]),
          "score": clamp_score(refl["score"], k6_max) if refl["assessed"] else None,
          "evidence": refl["evidence_quote"], "feedback": refl["feedback"]}
    if k6["assessed"] and not P.quote_supported(k6["evidence"], revised):
        k6.update(assessed=False, score=None)
        notes.append("K6: dalil qayta javob matnida topilmagani uchun baholanmadi.")
    return {
        "rubric_version": rubric.version, "criteria": criteria, "reflection": k6,
        "comparison": data["comparison"], "feedback": data["feedback"],
        "limitations": ["Baholash faqat matnli javob asosida bajarildi."] + data["limitations"] + notes,
    }
