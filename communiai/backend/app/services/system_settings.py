"""Runtime settings an administrator may change (stored in DB, never secrets)."""
import time
import uuid
from typing import Any

from app.core.database import SessionLocal
from app.models import SystemSetting

# key -> (type, description)
EDITABLE_SETTINGS: dict[str, tuple[type, str]] = {
    "ai_enabled": (bool, "AI operatsiyalarini yoqish/o'chirish (texnik xizmat rejimi)"),
    "ai_model": (str, "AI model identifikatori (bo'sh bo'lsa .env dagi AI_MODEL)"),
    "registration_open": (bool, "Yangi foydalanuvchilarni ro'yxatdan o'tkazish"),
}

_cache: dict[str, tuple[float, Any]] = {}
_TTL = 10.0


def get_setting(key: str, default: Any = None) -> Any:
    now = time.monotonic()
    hit = _cache.get(key)
    if hit and now - hit[0] < _TTL:
        return default if hit[1] is None else hit[1]
    try:
        with SessionLocal() as db:
            row = db.get(SystemSetting, key)
            value = row.value.get("v") if row else None
    except Exception:
        value = None
    _cache[key] = (now, value)
    return default if value is None else value


def set_setting(key: str, value: Any, actor_id: uuid.UUID) -> None:
    with SessionLocal() as db:
        row = db.get(SystemSetting, key)
        if row is None:
            db.add(SystemSetting(key=key, value={"v": value}, updated_by=actor_id))
        else:
            row.value = {"v": value}
            row.updated_by = actor_id
        db.commit()
    _cache.pop(key, None)


def all_settings() -> dict[str, Any]:
    return {k: get_setting(k) for k in EDITABLE_SETTINGS}


def clear_cache() -> None:
    _cache.clear()
