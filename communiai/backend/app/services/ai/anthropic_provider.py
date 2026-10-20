"""Anthropic (Claude) implementation of AIProvider using the official SDK and structured outputs."""
import logging
from typing import TypeVar

import anthropic
from pydantic import BaseModel, ValidationError

from app.services.ai.provider import (
    AIInvalidOutputError, AIProviderError, AIRefusedError, AITimeoutError, AIUnavailableError, AIUsage,
)

log = logging.getLogger("communiai.ai.anthropic")
T = TypeVar("T", bound=BaseModel)

# Server-side refusal fallback: if the primary model declines, the API retries on a
# suitable fallback model inside the same call.
FALLBACK_BETA = "server-side-fallback-2026-07-01"


class AnthropicProvider:
    name = "anthropic"

    def __init__(self, api_key: str, model: str, timeout: int, effort: str = "medium"):
        self.model = model
        self.effort = effort
        # SDK retries 408/409/429/5xx and connection errors itself (max_retries).
        self._client = anthropic.Anthropic(api_key=api_key, timeout=float(timeout), max_retries=2)

    def generate(self, *, system: str, user_content: str, schema: type[T], max_tokens: int) -> tuple[T, AIUsage]:
        try:
            response = self._client.beta.messages.parse(
                model=self.model,
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": user_content}],
                output_config={"effort": self.effort},
                output_format=schema,
                betas=[FALLBACK_BETA],
                fallbacks="default",
            )
        except anthropic.APITimeoutError as e:
            raise AITimeoutError("timeout") from e
        except anthropic.AuthenticationError as e:
            raise AIUnavailableError("authentication failed") from e
        except anthropic.PermissionDeniedError as e:
            raise AIUnavailableError("permission denied") from e
        except anthropic.NotFoundError as e:
            raise AIUnavailableError("model not found") from e
        except anthropic.BadRequestError as e:
            raise AIProviderError(f"bad request: {getattr(e, 'message', '')[:200]}") from e
        except anthropic.RateLimitError as e:
            raise AIProviderError("rate limited") from e
        except anthropic.APIStatusError as e:
            raise AIProviderError(f"status {e.status_code}") from e
        except anthropic.APIConnectionError as e:
            raise AIProviderError("connection error") from e
        except ValidationError as e:
            raise AIInvalidOutputError(f"schema validation failed: {e.error_count()} errors") from e
        except ValueError as e:  # JSON decode problems surface as ValueError
            raise AIInvalidOutputError("could not parse JSON output") from e

        usage = AIUsage(getattr(response.usage, "input_tokens", None), getattr(response.usage, "output_tokens", None))
        if response.stop_reason == "refusal":
            raise AIRefusedError("model refused")
        if response.stop_reason == "max_tokens":
            raise AIInvalidOutputError("output truncated (max_tokens)")
        parsed = response.parsed_output
        if parsed is None:
            raise AIInvalidOutputError("no structured output returned")
        # Re-validate explicitly so constraints (ranges, lengths) are enforced by our schema.
        try:
            obj = schema.model_validate(parsed.model_dump())
        except ValidationError as e:
            raise AIInvalidOutputError(f"schema validation failed: {e.error_count()} errors") from e
        return obj, usage
