"""Provider-independent AI interface.

Services depend only on `AIProvider`. Concrete providers are chosen by configuration
(AI_PROVIDER). There is deliberately no "fake"/demo provider in production code: if no
provider is configured, calls raise `AIUnavailableError` and the UI reports it honestly.
"""
import logging
import time
import uuid
from dataclasses import dataclass
from typing import Protocol, TypeVar

from pydantic import BaseModel

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.models import AIRequestLog

log = logging.getLogger("communiai.ai")

T = TypeVar("T", bound=BaseModel)


class AIError(Exception):
    code = "AI_ERROR"
    user_message = "AI xizmatida xatolik yuz berdi. Keyinroq qayta urinib ko'ring."
    retryable = True


class AIUnavailableError(AIError):
    code = "AI_NOT_CONFIGURED"
    user_message = "AI xizmati serverda sozlanmagan. Administratorga murojaat qiling."
    retryable = False


class AITimeoutError(AIError):
    code = "AI_TIMEOUT"
    user_message = "AI xizmati belgilangan vaqtda javob bermadi. Qayta urinib ko'ring."


class AIProviderError(AIError):
    code = "AI_PROVIDER_ERROR"


class AIInvalidOutputError(AIError):
    code = "AI_INVALID_OUTPUT"
    user_message = "AI javobi talab qilingan tuzilmaga mos kelmadi. Qayta urinib ko'ring."


class AIRefusedError(AIError):
    code = "AI_REFUSED"
    user_message = "AI ushbu so'rovni bajarishdan bosh tortdi. Matnni tekshirib, qayta urinib ko'ring."
    retryable = False


@dataclass
class AIUsage:
    input_tokens: int | None = None
    output_tokens: int | None = None


class AIProvider(Protocol):
    name: str
    model: str

    def generate(self, *, system: str, user_content: str, schema: type[T], max_tokens: int) -> tuple[T, AIUsage]:
        """Return a schema-validated object. Raise an AIError subclass on failure."""
        ...


class DisabledProvider:
    name = "disabled"

    def __init__(self, model: str = "-"):
        self.model = model

    def generate(self, *, system: str, user_content: str, schema: type[T], max_tokens: int) -> tuple[T, AIUsage]:
        raise AIUnavailableError("AI provider is not configured")


_override: AIProvider | None = None


def set_provider_override(provider: AIProvider | None) -> None:
    """Used by the test-suite to inject a scripted provider."""
    global _override
    _override = provider


def get_provider() -> AIProvider:
    if _override is not None:
        return _override
    s = get_settings()
    if not s.ai_configured:
        return DisabledProvider(s.AI_MODEL)
    if s.AI_PROVIDER == "anthropic":
        from app.services.ai.anthropic_provider import AnthropicProvider
        return AnthropicProvider(api_key=s.AI_API_KEY, model=_effective_model(s.AI_MODEL),
                                 timeout=s.AI_TIMEOUT_SECONDS, effort=s.AI_EFFORT)
    log.error("Unknown AI_PROVIDER=%s", s.AI_PROVIDER)
    return DisabledProvider(s.AI_MODEL)


def _effective_model(default: str) -> str:
    """Admin may override the model at runtime via system_settings."""
    from app.services.system_settings import get_setting
    return get_setting("ai_model", default) or default


def ai_enabled_by_admin() -> bool:
    from app.services.system_settings import get_setting
    return bool(get_setting("ai_enabled", True))


def call_structured(operation: str, *, system: str, user_content: str, schema: type[T],
                    user_id: uuid.UUID | None, max_tokens: int = 8000,
                    validator=None, max_attempts: int | None = None) -> T:
    """Call the provider with bounded retries on invalid structure, and log technical metrics.

    `validator(obj)` may raise AIInvalidOutputError to trigger a retry (e.g. missing evidence).
    """
    s = get_settings()
    if not ai_enabled_by_admin():
        raise AIUnavailableError("AI disabled by administrator")
    provider = get_provider()
    attempts = max_attempts or (s.AI_MAX_RETRIES + 1)
    last_error: AIError | None = None
    for attempt in range(1, attempts + 1):
        started = time.monotonic()
        status, err_type, usage = "ok", None, AIUsage()
        try:
            obj, usage = provider.generate(system=system, user_content=user_content, schema=schema,
                                           max_tokens=max_tokens)
            if validator is not None:
                validator(obj)
            return obj
        except AIInvalidOutputError as e:
            status, err_type, last_error = "invalid_output", type(e).__name__, e
            log.warning("AI %s attempt %d/%d invalid output: %s", operation, attempt, attempts, e)
            continue
        except AIError as e:
            status, err_type = "error", type(e).__name__
            raise
        except Exception as e:  # never leak provider internals; treat as provider error
            status, err_type = "error", type(e).__name__
            log.exception("AI %s unexpected error", operation)
            raise AIProviderError(str(type(e).__name__)) from e
        finally:
            _log_request(user_id, operation, provider, status, started, usage, err_type)
    raise last_error or AIInvalidOutputError("invalid output")


def _log_request(user_id, operation, provider, status, started, usage: AIUsage, err_type):
    try:
        with SessionLocal() as db:
            db.add(AIRequestLog(user_id=user_id, operation=operation, provider=provider.name,
                                model=provider.model, status=status,
                                latency_ms=int((time.monotonic() - started) * 1000),
                                input_tokens=usage.input_tokens, output_tokens=usage.output_tokens,
                                error_type=err_type))
            db.commit()
    except Exception:  # monitoring must never break the main flow
        log.exception("Failed to write AI request log")
