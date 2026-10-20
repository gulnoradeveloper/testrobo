"""Unit tests for the Anthropic adapter's mapping of SDK responses/errors (no network)."""
from types import SimpleNamespace

import anthropic
import httpx2
import pytest

from app.services.ai.anthropic_provider import AnthropicProvider
from app.services.ai.provider import (
    AIInvalidOutputError, AIProviderError, AIRefusedError, AITimeoutError, AIUnavailableError,
)
from app.services.ai.schemas import QuestionOut

Q = QuestionOut(question="Navbat raqami qanday beriladi?", question_type="main", focus_area="texnik",
                project_reference="Funksiyalar", rationale="r")


def _provider(monkeypatch, result=None, exc=None):
    p = AnthropicProvider(api_key="test-key", model="claude-opus-5-5", timeout=5)
    captured = {}

    def fake_parse(**kwargs):
        captured.update(kwargs)
        if exc:
            raise exc
        return result

    monkeypatch.setattr(p._client.beta.messages, "parse", fake_parse)
    return p, captured


def _resp(stop="end_turn", parsed=Q):
    return SimpleNamespace(stop_reason=stop, parsed_output=parsed,
                           usage=SimpleNamespace(input_tokens=10, output_tokens=5))


def test_success_and_request_shape(monkeypatch):
    p, captured = _provider(monkeypatch, _resp())
    obj, usage = p.generate(system="sys", user_content="u", schema=QuestionOut, max_tokens=100)
    assert obj.question == Q.question and usage.output_tokens == 5
    assert captured["model"] == "claude-opus-5-5"
    assert captured["output_format"] is QuestionOut
    assert captured["fallbacks"] == "default"
    assert "thinking" not in captured  # Opus 5.5: thinking is always on, controlled by effort
    assert captured["output_config"] == {"effort": "medium"}


@pytest.mark.parametrize("stop,parsed,err", [
    ("refusal", Q, AIRefusedError), ("max_tokens", Q, AIInvalidOutputError), ("end_turn", None, AIInvalidOutputError),
])
def test_bad_responses(monkeypatch, stop, parsed, err):
    p, _ = _provider(monkeypatch, _resp(stop, parsed))
    with pytest.raises(err):
        p.generate(system="s", user_content="u", schema=QuestionOut, max_tokens=10)


def _status_error(cls, code):
    req = httpx2.Request("POST", "https://api.anthropic.com/v1/messages")
    return cls("x", response=httpx2.Response(code, request=req), body=None)


@pytest.mark.parametrize("exc,err", [
    (lambda: anthropic.APITimeoutError(request=httpx2.Request("POST", "https://x")), AITimeoutError),
    (lambda: _status_error(anthropic.AuthenticationError, 401), AIUnavailableError),
    (lambda: _status_error(anthropic.RateLimitError, 429), AIProviderError),
    (lambda: _status_error(anthropic.InternalServerError, 500), AIProviderError),
])
def test_error_mapping(monkeypatch, exc, err):
    p, _ = _provider(monkeypatch, exc=exc())
    with pytest.raises(err):
        p.generate(system="s", user_content="u", schema=QuestionOut, max_tokens=10)

