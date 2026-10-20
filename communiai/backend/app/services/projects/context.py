"""Build the project context for AI prompts and a hash that identifies the project version."""
import hashlib
import json

from app.models import ExtractionStatus, Project

FIELD_LABELS = [
    ("title", "Loyiha nomi"), ("category", "Loyiha turi"), ("description", "Tavsif"),
    ("problem", "Hal qilinayotgan muammo"), ("objective", "Maqsad"), ("target_users", "Maqsadli foydalanuvchilar"),
    ("features", "Asosiy funksiyalar"), ("technologies", "Texnologiyalar"), ("innovation", "Innovatsion jihatlar"),
    ("expected_results", "Kutilayotgan natijalar"), ("future_plans", "Rivojlantirish rejalari"),
]

CATEGORY_LABELS = {
    "web": "Veb-ilova", "mobile": "Mobil ilova", "info_system": "Axborot tizimi", "ai": "Sun'iy intellekt loyihasi",
    "cybersecurity": "Kiberxavfsizlik loyihasi", "iot": "IoT", "robotics": "Robototexnika", "other": "Boshqa IT loyiha",
}

MAX_DOC_CHARS_TOTAL = 60_000


def _field_value(project: Project, name: str) -> str:
    v = getattr(project, name)
    if name == "category":
        return CATEGORY_LABELS.get(v.value if hasattr(v, "value") else v, str(v))
    return v or ""


def fields_text(project: Project) -> str:
    lines = []
    for name, label in FIELD_LABELS:
        value = _field_value(project, name).strip()
        lines.append(f"[{label}]\n{value if value else 'Kiritilmagan'}")
    return "\n\n".join(lines)


def documents_text(project: Project) -> str:
    parts, budget = [], MAX_DOC_CHARS_TOTAL
    for f in project.files:
        if f.extraction_status != ExtractionStatus.COMPLETED or not f.extracted_text or budget <= 0:
            continue
        chunk = f.extracted_text[:budget]
        budget -= len(chunk)
        parts.append(f"=== Hujjat: {f.original_filename} ===\n{chunk}")
    return "\n\n".join(parts)


def corpus(project: Project) -> str:
    """All project data the AI may cite (used to verify evidence quotes)."""
    return fields_text(project) + "\n\n" + documents_text(project)


def snapshot_hash(project: Project) -> str:
    data = {name: _field_value(project, name) for name, _ in FIELD_LABELS}
    data["files"] = sorted(
        [f.sha256, f.extraction_status.value] for f in project.files
    )
    return hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def has_minimum_data(project: Project) -> list[str]:
    missing = []
    for name, label in (("title", "Loyiha nomi"), ("description", "Tavsif"), ("problem", "Muammo")):
        if not (getattr(project, name) or "").strip():
            missing.append(label)
    return missing
