"""Konfiguratsiya — muhit o‘zgaruvchilari yoki .env fayli orqali (.env.example ga qarang)."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="BT_", env_file=".env", extra="ignore", protected_namespaces=())

    environment: str = "development"
    database_url: str = f"sqlite:///{PROJECT_ROOT / 'data' / 'bogimtahlil.db'}"
    storage_dir: Path = PROJECT_ROOT / "data" / "storage"

    model_path: Path = PROJECT_ROOT / "artifacts" / "model.pt"
    model_sha256: str | None = None  # ko‘rsatilsa, yuklashda tekshiriladi
    model_name: str = "Bo‘g‘imTahlil KL tasniflagichi"
    allow_untrained_model: bool = False  # FAQAT avtomatik testlar uchun
    device: str = "auto"
    torch_threads: int = 0  # 0 — PyTorch standarti

    max_upload_mb: int = 20
    max_image_pixels: int = 50_000_000
    min_image_side: int = 128
    retention_hours: int = 24
    cleanup_interval_minutes: int = 15

    rate_limit_analyses_per_minute: int = 10
    rate_limit_requests_per_minute: int = 240

    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173", "http://127.0.0.1:5173"])
    session_cookie_name: str = "bt_session"
    session_cookie_secure: bool = False  # HTTPS ostida true qiling
    force_https: bool = False
    trust_proxy_headers: bool = False

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()
