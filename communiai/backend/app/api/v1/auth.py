import logging
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.api.deps import audit, auth_rate_limit, get_current_user
from app.core.config import get_settings
from app.core.database import get_db
from app.core.errors import AppError
from app.core.security import (
    create_access_token, hash_password, hash_token, new_opaque_token, password_problems, verify_password,
)
from app.models import PasswordResetToken, RefreshToken, User, utcnow
from app.schemas import (
    LoginIn, PasswordResetConfirmIn, PasswordResetRequestIn, RefreshIn, RegisterIn, TokenOut, UserOut,
)
from app.services.email import EmailNotConfigured, send_email
from app.services.system_settings import get_setting

router = APIRouter(prefix="/auth", tags=["Authentication"])
log = logging.getLogger("communiai.auth")


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


def _issue_tokens(db: Session, user: User, family_id: uuid.UUID | None = None) -> TokenOut:
    s = get_settings()
    access, expires_in = create_access_token(user.id, user.role.value)
    refresh = new_opaque_token()
    db.add(RefreshToken(user_id=user.id, family_id=family_id or uuid.uuid4(), token_hash=hash_token(refresh),
                        expires_at=utcnow() + timedelta(days=s.REFRESH_TOKEN_DAYS)))
    return TokenOut(access_token=access, refresh_token=refresh, expires_in=expires_in,
                    user=UserOut.model_validate(user))


@router.post("/register", response_model=TokenOut, status_code=201, dependencies=[Depends(auth_rate_limit)])
def register(body: RegisterIn, db: Session = Depends(get_db)):
    if not get_setting("registration_open", True):
        raise AppError(403, "REGISTRATION_CLOSED", "Ro'yxatdan o'tish vaqtincha yopilgan")
    if body.password != body.password_confirm:
        raise AppError(422, "VALIDATION_ERROR", "Parollar mos kelmadi",
                       [{"field": "password_confirm", "message": "Parollar mos kelmadi"}])
    problems = password_problems(body.password, body.email, (body.first_name, body.last_name))
    if problems:
        raise AppError(422, "WEAK_PASSWORD", problems[0], [{"field": "password", "message": p} for p in problems])
    email = body.email.lower()
    if db.scalars(select(User).where(User.email == email)).first():
        raise AppError(409, "EMAIL_TAKEN", "Bu elektron pochta bilan foydalanuvchi allaqachon mavjud")
    user = User(first_name=body.first_name, last_name=body.last_name, email=email,
                password_hash=hash_password(body.password), university=body.university,
                study_program=body.study_program)
    db.add(user)
    db.flush()
    audit(db, user.id, "user.register", "user", user.id)
    tokens = _issue_tokens(db, user)
    db.commit()
    return tokens


@router.post("/login", response_model=TokenOut, dependencies=[Depends(auth_rate_limit)])
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = db.scalars(select(User).where(User.email == body.email.lower())).first()
    if user is None or not verify_password(body.password, user.password_hash):
        raise AppError(401, "INVALID_CREDENTIALS", "Elektron pochta yoki parol noto'g'ri")
    if not user.is_active:
        raise AppError(403, "ACCOUNT_DISABLED", "Hisob faol emas")
    audit(db, user.id, "user.login", "user", user.id)
    tokens = _issue_tokens(db, user)
    db.commit()
    return tokens


@router.post("/refresh", response_model=TokenOut, dependencies=[Depends(auth_rate_limit)])
def refresh(body: RefreshIn, db: Session = Depends(get_db)):
    row = db.scalars(select(RefreshToken).where(RefreshToken.token_hash == hash_token(body.refresh_token))).first()
    if row is None:
        raise AppError(401, "INVALID_REFRESH_TOKEN", "Refresh token yaroqsiz")
    if row.revoked_at is not None:
        # Reuse of a rotated token: assume theft, revoke the whole family.
        db.execute(update(RefreshToken).where(RefreshToken.family_id == row.family_id, RefreshToken.revoked_at.is_(None))
                   .values(revoked_at=utcnow()))
        audit(db, row.user_id, "auth.refresh_reuse_detected", "refresh_token", row.id)
        db.commit()
        raise AppError(401, "INVALID_REFRESH_TOKEN", "Refresh token qayta ishlatildi. Qaytadan kiring.")
    if _aware(row.expires_at) < utcnow():
        raise AppError(401, "INVALID_REFRESH_TOKEN", "Refresh token muddati tugagan")
    user = db.get(User, row.user_id)
    if user is None or not user.is_active:
        raise AppError(401, "UNAUTHORIZED", "Foydalanuvchi faol emas")
    row.revoked_at = utcnow()
    tokens = _issue_tokens(db, user, family_id=row.family_id)
    db.commit()
    return tokens


@router.post("/logout", status_code=204)
def logout(body: RefreshIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    row = db.scalars(select(RefreshToken).where(RefreshToken.token_hash == hash_token(body.refresh_token),
                                                RefreshToken.user_id == user.id)).first()
    if row and row.revoked_at is None:
        row.revoked_at = utcnow()
    audit(db, user.id, "user.logout", "user", user.id)
    db.commit()


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


@router.post("/password-reset/request", status_code=202, dependencies=[Depends(auth_rate_limit)])
def password_reset_request(body: PasswordResetRequestIn, db: Session = Depends(get_db)):
    s = get_settings()
    if not s.email_enabled:
        raise AppError(503, "EMAIL_NOT_CONFIGURED",
                       "Parolni tiklash uchun email xizmati serverda sozlanmagan. Administratorga murojaat qiling.")
    user = db.scalars(select(User).where(User.email == body.email.lower(), User.is_active.is_(True))).first()
    if user is not None:
        token = new_opaque_token()
        db.add(PasswordResetToken(user_id=user.id, token_hash=hash_token(token),
                                  expires_at=utcnow() + timedelta(minutes=s.PASSWORD_RESET_TOKEN_MINUTES)))
        db.commit()
        try:
            send_email(user.email, "CommuniAI — parolni tiklash",
                       f"Assalomu alaykum, {user.first_name}!\n\nParolni tiklash kodi:\n\n{token}\n\n"
                       f"Kod {s.PASSWORD_RESET_TOKEN_MINUTES} daqiqa amal qiladi. Agar bu so'rovni siz "
                       "yubormagan bo'lsangiz, xabarni e'tiborsiz qoldiring.")
        except EmailNotConfigured:
            raise AppError(503, "EMAIL_NOT_CONFIGURED", "Email xizmati sozlanmagan") from None
        except Exception:
            log.exception("Password reset e-mail failed")
            raise AppError(502, "EMAIL_SEND_FAILED", "Email yuborib bo'lmadi. Keyinroq qayta urinib ko'ring.") from None
    # Same response whether or not the e-mail exists (prevents account enumeration).
    return {"message": "Agar bu pochta ro'yxatdan o'tgan bo'lsa, tiklash kodi yuborildi."}


@router.post("/password-reset/confirm", dependencies=[Depends(auth_rate_limit)])
def password_reset_confirm(body: PasswordResetConfirmIn, db: Session = Depends(get_db)):
    if body.new_password != body.new_password_confirm:
        raise AppError(422, "VALIDATION_ERROR", "Parollar mos kelmadi")
    row = db.scalars(select(PasswordResetToken).where(PasswordResetToken.token_hash == hash_token(body.token))).first()
    if row is None or row.used_at is not None or _aware(row.expires_at) < utcnow():
        raise AppError(400, "INVALID_RESET_TOKEN", "Tiklash kodi yaroqsiz yoki muddati tugagan")
    user = db.get(User, row.user_id)
    problems = password_problems(body.new_password, user.email, (user.first_name, user.last_name))
    if problems:
        raise AppError(422, "WEAK_PASSWORD", problems[0])
    user.password_hash = hash_password(body.new_password)
    row.used_at = utcnow()
    db.execute(update(RefreshToken).where(RefreshToken.user_id == user.id, RefreshToken.revoked_at.is_(None))
               .values(revoked_at=utcnow()))
    audit(db, user.id, "user.password_reset", "user", user.id)
    db.commit()
    return {"message": "Parol yangilandi. Yangi parol bilan tizimga kiring."}
