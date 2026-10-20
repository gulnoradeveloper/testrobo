"""Application settings loaded from environment variables (.env supported)."""
from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"

    DATABASE_URL: str = "postgresql+psycopg://communiai:communiai@localhost:5432/communiai"

    JWT_SECRET: str = Field(default="change-me-in-env", min_length=16)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_MINUTES: int = 15
    REFRESH_TOKEN_DAYS: int = 30

    # AI provider: "anthropic" (implemented) or "disabled".
    AI_PROVIDER: str = "anthropic"
    AI_API_KEY: str = ""
    AI_MODEL: str = "claude-opus-5-5"
    AI_TIMEOUT_SECONDS: int = 120
    AI_MAX_RETRIES: int = 2
    AI_EFFORT: str = "medium"

    MAX_UPLOAD_SIZE_MB: int = 20
    MAX_EXTRACTED_CHARS: int = 200_000
    MAX_ARCHIVE_UNCOMPRESSED_MB: int = 150
    MAX_ARCHIVE_ENTRIES: int = 5000

    FILE_STORAGE_BACKEND: str = "local"  # local | s3
    LOCAL_STORAGE_DIR: str = "./storage"
    STORAGE_BUCKET: str = ""
    S3_ENDPOINT_URL: str = ""
    S3_REGION: str = "us-east-1"
    S3_ACCESS_KEY_ID: str = ""
    S3_SECRET_ACCESS_KEY: str = ""

    CORS_ALLOWED_ORIGINS: str = ""

    # Password reset e-mail (SMTP). Empty SMTP_HOST => feature reported as unavailable.
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = ""
    SMTP_USE_TLS: bool = True
    PASSWORD_RESET_TOKEN_MINUTES: int = 30

    RATE_LIMIT_PER_MINUTE: int = 120
    AUTH_RATE_LIMIT_PER_MINUTE: int = 10
    AI_RATE_LIMIT_PER_MINUTE: int = 20

    RUBRIC_VERSION: str = "1.0"
    # "thread" runs AI jobs on a background thread pool, "inline" runs them in-request (tests).
    JOB_EXECUTION: str = "thread"
    JOB_WORKERS: int = 4

    @field_validator("FILE_STORAGE_BACKEND")
    @classmethod
    def _storage(cls, v: str) -> str:
        if v not in {"local", "s3"}:
            raise ValueError("FILE_STORAGE_BACKEND must be 'local' or 's3'")
        return v

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.CORS_ALLOWED_ORIGINS.split(",") if o.strip()]

    @property
    def max_upload_bytes(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    @property
    def email_enabled(self) -> bool:
        return bool(self.SMTP_HOST and self.SMTP_FROM)

    @property
    def ai_configured(self) -> bool:
        return self.AI_PROVIDER != "disabled" and bool(self.AI_API_KEY)


@lru_cache
def get_settings() -> Settings:
    return Settings()
