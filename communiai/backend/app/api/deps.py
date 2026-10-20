import threading
import time
import uuid
from collections import defaultdict, deque

import jwt
from fastapi import Depends, Header, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.errors import AppError, forbidden, not_found
from app.core.security import decode_access_token
from app.models import AuditLog, DefenseSession, IdempotencyRecord, Project, User, UserRole

_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer), db: Session = Depends(get_db)
) -> User:
    if creds is None or creds.scheme.lower() != "bearer":
        raise AppError(401, "UNAUTHORIZED", "Avtorizatsiya talab qilinadi")
    try:
        payload = decode_access_token(creds.credentials)
        user_id = uuid.UUID(payload["sub"])
    except (jwt.ExpiredSignatureError,):
        raise AppError(401, "TOKEN_EXPIRED", "Sessiya muddati tugagan") from None
    except (jwt.InvalidTokenError, KeyError, ValueError):
        raise AppError(401, "UNAUTHORIZED", "Token yaroqsiz") from None
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise AppError(401, "UNAUTHORIZED", "Foydalanuvchi faol emas")
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != UserRole.ADMIN:
        raise forbidden("Faqat administrator uchun")
    return user


def require_ai_consent(user: User = Depends(get_current_user)) -> User:
    if user.ai_consent_at is None:
        raise AppError(403, "AI_CONSENT_REQUIRED",
                       "AI tahlili uchun ma'lumotlaringizni AI xizmatiga yuborishga rozilik bering")
    return user


# ---------------------------------------------------------------- ownership helpers
def owned_project(db: Session, project_id: uuid.UUID, user: User) -> Project:
    project = db.get(Project, project_id)
    if project is None or project.deleted_at is not None or project.owner_id != user.id:
        # Same response for "missing" and "someone else's" to avoid leaking existence.
        raise not_found("Loyiha")
    return project


def owned_session(db: Session, session_id: uuid.UUID, user: User) -> DefenseSession:
    s = db.get(DefenseSession, session_id)
    if s is None or s.user_id != user.id:
        raise not_found("Himoya sessiyasi")
    return s


# ---------------------------------------------------------------- pagination
class Page:
    def __init__(self, page: int = 1, page_size: int = 20):
        if page < 1 or page_size < 1 or page_size > 100:
            raise AppError(422, "VALIDATION_ERROR", "page >= 1 va 1 <= page_size <= 100 bo'lishi kerak")
        self.page, self.page_size = page, page_size

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    def wrap(self, items: list, total: int) -> dict:
        return {"items": items, "total": total, "page": self.page, "page_size": self.page_size}


# ---------------------------------------------------------------- rate limiting
class RateLimiter:
    """In-process sliding-window limiter. For multi-instance deployments use a shared store (Redis)."""

    def __init__(self):
        self._hits: dict[str, deque] = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, key: str, limit: int, window: float = 60.0) -> None:
        now = time.monotonic()
        with self._lock:
            q = self._hits[key]
            while q and now - q[0] > window:
                q.popleft()
            if len(q) >= limit:
                retry = int(window - (now - q[0])) + 1
                raise AppError(429, "RATE_LIMITED", "So'rovlar soni juda ko'p. Birozdan so'ng qayta urinib ko'ring.",
                               {"retry_after_seconds": retry})
            q.append(now)

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


limiter = RateLimiter()


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def auth_rate_limit(request: Request) -> None:
    limiter.check(f"auth:{_client_ip(request)}:{request.url.path}", get_settings().AUTH_RATE_LIMIT_PER_MINUTE)


def ai_rate_limit(user: User = Depends(get_current_user)) -> None:
    limiter.check(f"ai:{user.id}", get_settings().AI_RATE_LIMIT_PER_MINUTE)


# ---------------------------------------------------------------- idempotency
IdempotencyKey = Header(default=None, alias="Idempotency-Key", max_length=100)


def idem_get(db: Session, user: User, key: str | None, endpoint: str) -> IdempotencyRecord | None:
    if not key:
        return None
    return db.scalars(select(IdempotencyRecord).where(
        IdempotencyRecord.user_id == user.id, IdempotencyRecord.key == key, IdempotencyRecord.endpoint == endpoint
    )).first()


def idem_save(db: Session, user: User, key: str | None, endpoint: str, status_code: int, body: dict) -> None:
    if key:
        db.add(IdempotencyRecord(user_id=user.id, key=key, endpoint=endpoint, status_code=status_code,
                                 response_json=body))


# ---------------------------------------------------------------- audit
def audit(db: Session, actor_id: uuid.UUID | None, action: str, resource_type: str, resource_id=None,
          details: dict | None = None) -> None:
    db.add(AuditLog(actor_id=actor_id, action=action, resource_type=resource_type,
                    resource_id=str(resource_id) if resource_id else None, details=details))
