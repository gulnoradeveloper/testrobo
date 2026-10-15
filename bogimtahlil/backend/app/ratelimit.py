"""Oddiy xotiradagi rate limiting (bitta jarayon uchun; ko‘p nusxali joylashtirishda Redis kabi umumiy saqlash kerak)."""
from __future__ import annotations

import threading
import time
from collections import defaultdict, deque

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .errors import error_body
from .messages import ERRORS


class SlidingWindowLimiter:
    def __init__(self) -> None:
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, key: str, limit: int, window: float = 60.0) -> tuple[bool, int]:
        now = time.monotonic()
        with self._lock:
            q = self._hits[key]
            while q and now - q[0] > window:
                q.popleft()
            if len(q) >= limit:
                return False, int(window - (now - q[0])) + 1
            q.append(now)
            if len(self._hits) > 50_000:  # xotira o‘sishini cheklash
                for k in [k for k, v in self._hits.items() if not v]:
                    del self._hits[k]
            return True, 0


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, settings):
        super().__init__(app)
        self.settings = settings
        self.limiter = SlidingWindowLimiter()

    def _client(self, request: Request) -> str:
        if self.settings.trust_proxy_headers:
            fwd = request.headers.get("x-forwarded-for")
            if fwd:
                return fwd.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/api/"):
            ip = self._client(request)
            checks = [(f"all:{ip}", self.settings.rate_limit_requests_per_minute)]
            if request.method == "POST" and request.url.path.rstrip("/") == "/api/v1/analyses":
                checks.append((f"analyze:{ip}", self.settings.rate_limit_analyses_per_minute))
            for key, limit in checks:
                ok, retry = self.limiter.allow(key, limit)
                if not ok:
                    return JSONResponse(error_body("RATE_LIMITED", ERRORS["RATE_LIMITED"]), status_code=429,
                                        headers={"Retry-After": str(retry)})
        return await call_next(request)
