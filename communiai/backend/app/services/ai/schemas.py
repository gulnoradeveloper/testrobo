"""Pydantic schemas for every structured AI output. All AI responses are validated against these."""
from typing import Literal

from pydantic import BaseModel, Field, field_validator

Priority = Literal["Yuqori", "O'rta", "Past"]
RecCategory = Literal[
    "problem_goal", "functionality", "ux", "architecture", "security_privacy", "innovation",
    "effectiveness_evidence", "presentation",
]
DimensionStatus = Literal["yetarli", "qisman", "aniqlanmadi"]

ANALYSIS_DIMENSIONS = (
    "Muammoning aniq bayon etilishi", "Loyihaning maqsadi", "Taklif etilayotgan yechim",
    "Foydalanuvchi ehtiyojlariga moslik", "Texnik yondashuvning tushuntirilishi",
    "Asosiy funksiyalarning tavsifi", "Innovatsion jihatlarni asoslash", "Amaliy ahamiyat",
    "Mavjud kamchilik va xavflar", "Taqdimotning tayyorgarlik holati",
)


class Strength(BaseModel):
    title: str
    explanation: str
    evidence_quote: str = Field(description="Exact short quote from the PROJECT DATA supporting this strength")


class Weakness(BaseModel):
    problem: str
    location: str = Field(description="Where it was found (field name or document), or 'Hujjatda aniqlanmadi'")
    why_important: str
    how_to_fix: str


class ImprovementGroups(BaseModel):
    immediate: list[str]
    important: list[str]
    future: list[str]


class ExpectedQuestion(BaseModel):
    question: str
    rationale: str


class DimensionAssessment(BaseModel):
    dimension: str
    status: DimensionStatus
    comment: str


class ProjectRecommendation(BaseModel):
    category: RecCategory
    title: str
    problem: str
    solution: str
    priority: Priority
    steps: list[str]
    expected_result: str
    based_on: str = Field(description="Which project data or answer this recommendation is based on")


class ProjectAnalysisOut(BaseModel):
    summary: str
    strengths: list[Strength]
    weaknesses: list[Weakness]
    improvements: ImprovementGroups
    expected_questions: list[ExpectedQuestion]
    defense_tips: list[str]
    missing_information: list[str]
    dimensions: list[DimensionAssessment]
    project_recommendations: list[ProjectRecommendation]

    @field_validator("expected_questions")
    @classmethod
    def _min_questions(cls, v):
        if len(v) < 5:
            raise ValueError("at least 5 expected questions required")
        return v


class QuestionOut(BaseModel):
    question: str = Field(min_length=10)
    question_type: Literal["main", "follow_up"]
    focus_area: str
    project_reference: str = Field(description="Which project data the question relies on")
    rationale: str


class CriterionScore(BaseModel):
    code: Literal["K1", "K2", "K3", "K4", "K5"]
    assessed: bool
    score: int = Field(ge=0, le=20)
    evidence_quote: str = Field(description="Exact quote from the student's answer; empty if not assessed")
    feedback: str
    recommendation: str
    confidence_limit: str


class Readiness(BaseModel):
    assessed: bool
    score: int = Field(ge=0, le=10)
    comment: str


class AnswerFeedback(BaseModel):
    strength: str
    main_weakness: str
    why_important: str
    how_to_improve: str
    model_answer: str
    retry_task: str


class AnswerEvaluationOut(BaseModel):
    criteria: list[CriterionScore]
    content_readiness: Readiness
    technical_note: str
    feedback: AnswerFeedback
    limitations: list[str]
    needs_follow_up: bool
    follow_up_reason: str

    @field_validator("criteria")
    @classmethod
    def _all_codes(cls, v):
        codes = sorted(c.code for c in v)
        if codes != ["K1", "K2", "K3", "K4", "K5"]:
            raise ValueError("criteria must contain K1..K5 exactly once")
        return v


class Exercise(BaseModel):
    competency: Literal["K1", "K2", "K3", "K4", "K5"]
    title: str
    task: str
    question_sequence: int = Field(ge=1, description="Sequence number of the defense question to re-answer")
    success_criteria: list[str]


class FinalCoachOut(BaseModel):
    overall_summary: str
    strengths: list[str]
    weaknesses: list[str]
    detailed_analysis: str
    exercises: list[Exercise]
    project_recommendations: list[ProjectRecommendation]
    limitations: list[str]


class Reflection(BaseModel):
    assessed: bool
    score: int = Field(ge=0, le=10)
    evidence_quote: str
    feedback: str


class Comparison(BaseModel):
    improved_aspects: list[str]
    remaining_issues: list[str]
    summary: str


class PracticeEvaluationOut(BaseModel):
    criteria: list[CriterionScore]
    reflection: Reflection
    comparison: Comparison
    feedback: AnswerFeedback
    limitations: list[str]

    @field_validator("criteria")
    @classmethod
    def _all_codes(cls, v):
        if sorted(c.code for c in v) != ["K1", "K2", "K3", "K4", "K5"]:
            raise ValueError("criteria must contain K1..K5 exactly once")
        return v
