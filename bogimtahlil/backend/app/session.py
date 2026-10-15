"""Anonim sessiya: brauzerga tasodifiy token (HttpOnly cookie), bazaga esa uning SHA-256 qiymati yoziladi."""
from __future__ import annotations

import hashlib
import secrets

from fastapi import Request, Response

from .config import Settings


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def get_or_create_session(request: Request, response: Response, settings: Settings) -> str:
    token = request.cookies.get(settings.session_cookie_name)
    if not token or len(token) < 32 or len(token) > 128:
        token = secrets.token_urlsafe(32)
        response.set_cookie(
            settings.session_cookie_name, token, httponly=True, samesite="lax",
            secure=settings.session_cookie_secure, max_age=settings.retention_hours * 3600, path="/",
        )
    return _hash(token)
