"""Versioned communicative-competence rubric and backend-side score aggregation.

The AI only returns per-criterion scores with evidence. Totals, coverage and levels are
computed here so the model can never set an overall score itself.
"""
from dataclasses import dataclass

from app.core.errors import AppError


@dataclass(frozen=True)
class Criterion:
    code: str
    title: str
    max_score: int
    description: str


@dataclass(frozen=True)
class Level:
    min_percent: float
    name: str


@dataclass(frozen=True)
class Rubric:
    version: str
    criteria: tuple[Criterion, ...]
    levels: tuple[Level, ...]  # sorted from highest threshold to lowest

    @property
    def max_total(self) -> int:
        return sum(c.max_score for c in self.criteria)

    def criterion(self, code: str) -> Criterion:
        for c in self.criteria:
            if c.code == code:
                return c
        raise KeyError(code)

    def level_for(self, percent: float) -> str:
        for lvl in self.levels:
            if percent >= lvl.min_percent:
                return lvl.name
        return self.levels[-1].name


RUBRICS: dict[str, Rubric] = {
    "1.0": Rubric(
        version="1.0",
        criteria=(
            Criterion("K1", "Kasbiy fikrni aniq va tushunarli ifodalash", 20,
                      "Fikr aniq, ortiqcha so'zlarsiz va tushunarli bayon qilingan."),
            Criterion("K2", "Savolni tushunish va mazmunli javob berish", 20,
                      "Javob aynan berilgan savolga qaratilgan va mazmunli."),
            Criterion("K3", "Texnik qarorni dalillar bilan asoslash", 20,
                      "Texnik qarorlar sabablar, dalillar yoki muqobillar bilan asoslangan."),
            Criterion("K4", "Fikrning mantiqiy izchilligi va tuzilishi", 15,
                      "Javob mantiqiy ketma-ketlikda, aniq tuzilma bilan berilgan."),
            Criterion("K5", "Auditoriyaga mos kommunikatsiya", 15,
                      "Til va tushuntirish darajasi tanlangan auditoriyaga (rejimga) mos."),
            Criterion("K6", "Refleksiya va feedback asosida javobni takomillashtirish", 10,
                      "Feedbackdan so'ng qayta javob sifatining o'zgarishi. Faqat qayta mashqda baholanadi."),
        ),
        # Initial research thresholds (percent of applicable maximum). Not a validated instrument.
        levels=(Level(86, "Yetuk"), Level(71, "Mas'uliyatli"), Level(56, "Shakllanayotgan"), Level(0, "Intiluvchan")),
    )
}

PER_ANSWER_CODES = ("K1", "K2", "K3", "K4", "K5")
REFLECTION_CODE = "K6"


def get_rubric(version: str) -> Rubric:
    try:
        return RUBRICS[version]
    except KeyError as exc:
        raise AppError(500, "RUBRIC_NOT_FOUND", f"Rubrika versiyasi topilmadi: {version}") from exc


def clamp_score(score: float, max_score: int) -> float:
    return max(0.0, min(float(score), float(max_score)))


def aggregate(rubric: Rubric, per_answer: list[list[dict]], reflection: list[dict] | None = None) -> dict:
    """Aggregate criterion results.

    per_answer: for each answer, list of criterion dicts {code, score, assessed, evidence, ...}.
    reflection: optional K6 results from practice attempts.
    Criteria never assessed are reported as not assessed (not as 0) and excluded from the
    applicable maximum.
    """
    by_code: dict[str, list[dict]] = {c.code: [] for c in rubric.criteria}
    for answer_criteria in per_answer:
        for item in answer_criteria:
            if item.get("assessed") and item.get("code") in by_code and item.get("code") != REFLECTION_CODE:
                by_code[item["code"]].append(item)
    for item in reflection or []:
        if item.get("assessed"):
            by_code[REFLECTION_CODE].append(item)

    criteria_out = []
    total = 0.0
    max_applicable = 0
    for c in rubric.criteria:
        items = by_code[c.code]
        if items:
            mean = sum(clamp_score(i["score"], c.max_score) for i in items) / len(items)
            score = round(mean, 1)
            total += score
            max_applicable += c.max_score
            evidence = [i.get("evidence", "") for i in items if i.get("evidence")][:3]
            criteria_out.append({
                "code": c.code, "title": c.title, "score": score, "max_score": c.max_score,
                "assessed": True, "observations": len(items), "evidence": evidence,
                "percent": round(100 * score / c.max_score, 1),
            })
        else:
            criteria_out.append({
                "code": c.code, "title": c.title, "score": None, "max_score": c.max_score,
                "assessed": False, "observations": 0, "evidence": [], "percent": None,
                "status_label": "Hali baholanmagan",
            })

    total = round(total, 1)
    percent = round(100 * total / max_applicable, 1) if max_applicable else 0.0
    coverage = round(max_applicable / rubric.max_total, 3)
    return {
        "rubric_version": rubric.version,
        "criteria": criteria_out,
        "total_score": total,
        "max_applicable_score": max_applicable,
        "percent": percent,
        "coverage": coverage,
        "level": rubric.level_for(percent) if max_applicable else "Baholanmagan",
    }


def weakest_criteria(aggregated: dict, n: int = 2) -> list[str]:
    assessed = [c for c in aggregated["criteria"] if c["assessed"] and c["code"] != REFLECTION_CODE]
    assessed.sort(key=lambda c: (c["percent"], c["code"]))
    return [c["code"] for c in assessed[:n]]


def aggregate_readiness(items: list[dict]) -> dict:
    """Separate diagnostic indicator: technical/content presentation readiness (0-10 per answer)."""
    scored = [i for i in items if i.get("assessed")]
    if not scored:
        return {"assessed": False, "percent": None, "observations": 0, "notes": []}
    mean = sum(max(0, min(10, i["score"])) for i in scored) / len(scored)
    return {
        "assessed": True,
        "percent": round(mean * 10, 1),
        "observations": len(scored),
        "notes": [i.get("comment", "") for i in scored if i.get("comment")][:5],
    }
