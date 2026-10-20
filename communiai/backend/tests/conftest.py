import os
import re

# Always use a dedicated test database: the suite truncates every table.
os.environ["DATABASE_URL"] = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+psycopg://communiai:communiai@localhost:5432/communiai_test")
os.environ["JOB_EXECUTION"] = "inline"
os.environ["JWT_SECRET"] = "test-secret-test-secret-1234567890"
os.environ["AI_PROVIDER"] = "anthropic"
os.environ["AI_API_KEY"] = ""
os.environ["LOCAL_STORAGE_DIR"] = "/tmp/communiai-test-storage"
os.environ["AUTH_RATE_LIMIT_PER_MINUTE"] = "1000"
os.environ["AI_RATE_LIMIT_PER_MINUTE"] = "1000"
os.environ["RATE_LIMIT_PER_MINUTE"] = "100000"
os.environ["SMTP_HOST"] = ""

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

from app.api.deps import limiter  # noqa: E402
from app.core.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.services.ai import schemas as S  # noqa: E402
from app.services.ai.provider import AIUsage, set_provider_override  # noqa: E402
from app.services.system_settings import clear_cache  # noqa: E402

Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)


def _untrusted(content: str, source: str) -> str:
    m = re.search(rf'<untrusted_data source="{re.escape(source)}">\n(.*?)\n</untrusted_data>', content, re.S)
    return m.group(1) if m else ""


class ScriptedProvider:
    """Test double for the AI provider. Produces schema-valid outputs derived from the prompt so tests
    exercise the real prompt building, validation and post-processing code. Never used in production."""

    name = "scripted"
    model = "scripted-test-model"

    def __init__(self):
        self.calls: list[dict] = []
        self.queue: dict[str, list] = {}   # schema name -> list of exceptions / objects / callables to use first
        self.score = 14

    def push(self, schema_name: str, item):
        self.queue.setdefault(schema_name, []).append(item)

    def generate(self, *, system, user_content, schema, max_tokens):
        self.calls.append({"schema": schema.__name__, "system": system, "user": user_content})
        q = self.queue.get(schema.__name__)
        if q:
            item = q.pop(0)
            if isinstance(item, Exception):
                raise item
            if callable(item):
                item = item(user_content)
            return schema.model_validate(item), AIUsage(10, 10)
        return getattr(self, "_" + schema.__name__)(user_content), AIUsage(100, 50)

    # --- default generators
    def _ProjectAnalysisOut(self, content):
        fields = _untrusted(content, "project_fields")
        title = re.search(r"\[Loyiha nomi\]\n(.+)", fields).group(1)
        problem = re.search(r"\[Hal qilinayotgan muammo\]\n(.+)", fields).group(1)
        return S.ProjectAnalysisOut(
            summary=f"{title} loyihasi tahlil qilindi.",
            strengths=[S.Strength(title="Muammo aniq", explanation="Muammo bayon qilingan.", evidence_quote=problem[:40]),
                       S.Strength(title="Nom", explanation="Nom aniq.", evidence_quote=title)],
            weaknesses=[S.Weakness(problem="Testlash yo'q", location="Hujjatda aniqlanmadi", why_important="Ishonch",
                                   how_to_fix="Test natijalarini qo'shing")],
            improvements=S.ImprovementGroups(immediate=["a"], important=["b"], future=["c"]),
            expected_questions=[S.ExpectedQuestion(question=f"{title} haqida savol {i}?", rationale="r") for i in range(5)],
            defense_tips=["Arxitekturani tushuntiring"], missing_information=["Testlash natijalari"],
            dimensions=[S.DimensionAssessment(dimension=d, status="qisman", comment="-") for d in S.ANALYSIS_DIMENSIONS],
            project_recommendations=[S.ProjectRecommendation(
                category="architecture", title="Arxitektura", problem="p", solution="s", priority="Yuqori",
                steps=["1"], expected_result="e", based_on="Texnologiyalar maydoni")],
        )

    def _QuestionOut(self, content):
        n = len(re.findall(r"^Q\d+ \[", content, re.M)) + 1
        fields = _untrusted(content, "project_fields")
        title = re.search(r"\[Loyiha nomi\]\n(.+)", fields).group(1)
        return S.QuestionOut(question=f"{title}: {n}-savol — takroriy navbat raqamlarining oldi qanday olinadi?",
                             question_type="follow_up" if n > 1 else "main", focus_area="texnik imkoniyatlar",
                             project_reference="Asosiy funksiyalar", rationale="test")

    def _criteria(self, answer):
        quote = answer[: min(30, len(answer))]
        return [S.CriterionScore(code=c, assessed=True, score=self.score if c in ("K1", "K2", "K3") else 10,
                                 evidence_quote=quote, feedback="f", recommendation="r", confidence_limit="-")
                for c in ("K1", "K2", "K3", "K4", "K5")]

    def _feedback(self):
        return S.AnswerFeedback(strength="s", main_weakness="w", why_important="y", how_to_improve="h",
                                model_answer="Namuna javob", retry_task="Qayta ifodalang")

    def _AnswerEvaluationOut(self, content):
        answer = _untrusted(content, "student_answer")
        return S.AnswerEvaluationOut(criteria=self._criteria(answer),
                                     content_readiness=S.Readiness(assessed=True, score=6, comment="ok"),
                                     technical_note="t", feedback=self._feedback(), limitations=[],
                                     needs_follow_up=False, follow_up_reason="")

    def _FinalCoachOut(self, content):
        m = re.search(r"TARGET COMPETENCIES FOR EXERCISES \(weakest\): (.+)", content)
        targets = [t.strip() for t in m.group(1).split(",")] if m and m.group(1) != "none" else []
        return S.FinalCoachOut(
            overall_summary="Umumiy xulosa", strengths=["a"], weaknesses=["Dalillash yetarli emas"],
            detailed_analysis="- tahlil",
            exercises=[S.Exercise(competency=t, title=f"{t} mashqi", task="Qayta javob bering", question_sequence=1,
                                  success_criteria=["aniq"]) for t in targets],
            project_recommendations=[], limitations=[])

    def _PracticeEvaluationOut(self, content):
        revised = _untrusted(content, "revised_answer")
        crit = self._criteria(revised)
        for c in crit:
            c.score = min(c.score + 3, 15)
        return S.PracticeEvaluationOut(
            criteria=crit, reflection=S.Reflection(assessed=True, score=8, evidence_quote=revised[:20], feedback="ok"),
            comparison=S.Comparison(improved_aspects=["aniqroq"], remaining_issues=[], summary="yaxshilandi"),
            feedback=self._feedback(), limitations=[])


@pytest.fixture(autouse=True)
def _clean_db():
    with engine.begin() as conn:
        if engine.dialect.name == "sqlite":
            for t in reversed(Base.metadata.sorted_tables):
                conn.execute(t.delete())
        else:
            tables = ", ".join(t.name for t in reversed(Base.metadata.sorted_tables))
            conn.execute(text(f"TRUNCATE {tables} CASCADE"))
    limiter.reset()
    clear_cache()
    yield
    set_provider_override(None)


@pytest.fixture
def ai():
    p = ScriptedProvider()
    set_provider_override(p)
    yield p
    set_provider_override(None)


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


PASSWORD = "Kuchli-Parol-2026!"


def register(client, email="talaba@example.uz", consent=True):
    r = client.post("/api/v1/auth/register", json={
        "first_name": "Aziza", "last_name": "Karimova", "email": email, "password": PASSWORD,
        "password_confirm": PASSWORD, "university": "TATU", "study_program": "60610100"})
    assert r.status_code == 201, r.text
    tok = r.json()
    headers = {"Authorization": f"Bearer {tok['access_token']}"}
    if consent:
        assert client.patch("/api/v1/me", json={"ai_consent": True}, headers=headers).status_code == 200
    return headers, tok


PROJECT = {
    "title": "SmartQueue — elektron navbat tizimi",
    "category": "info_system",
    "description": "Talabalar uchun dekanatga elektron navbat olish tizimi. Navbat raqami SMS orqali yuboriladi.",
    "problem": "Dekanat oldida uzun navbatlar va vaqt yo'qotilishi muammosi mavjud.",
    "objective": "Navbat kutish vaqtini kamaytirish",
    "technologies": "Flutter, FastAPI, PostgreSQL",
}


def create_project(client, headers, **over):
    r = client.post("/api/v1/projects", json={**PROJECT, **over}, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()
