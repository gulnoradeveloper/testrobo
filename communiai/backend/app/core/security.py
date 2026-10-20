"""Password hashing (Argon2id), JWT access tokens, opaque refresh tokens."""
import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from app.core.config import get_settings

_hasher = PasswordHasher()  # argon2-cffi defaults to Argon2id

# Common weak passwords (lower-case). Checked in addition to length rules.
COMMON_PASSWORDS = {
    "1234567890", "12345678910", "0123456789", "qwertyuiop", "password", "password1", "password12",
    "password123", "password1234", "passw0rd123", "iloveyou12", "qwerty1234", "qwerty12345",
    "1q2w3e4r5t", "1qaz2wsx3edc", "asdfghjkl1", "zxcvbnm123", "abc1234567", "abcdefghij",
    "admin12345", "administrator", "welcome123", "letmein123", "monkey12345", "football12",
    "baseball12", "dragon1234", "sunshine12", "princess12", "superman12", "11111111111",
    "1111111111", "0000000000", "2222222222", "9999999999", "1234512345", "9876543210",
    "parol12345", "parol123456", "qwerty123456", "123456789a", "a123456789", "123456789q",
    "q123456789", "1234567890a", "toshkent123", "uzbekistan", "uzbekistan1", "o'zbekiston",
    "talaba12345", "student123", "student1234", "communiai1", "communiai123", "changeme123",
}


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except (VerificationError, InvalidHashError):
        return False


def password_problems(password: str, email: str = "", names: tuple[str, ...] = ()) -> list[str]:
    problems: list[str] = []
    if len(password) < 10:
        problems.append("Parol kamida 10 ta belgidan iborat bo'lishi kerak")
    low = password.lower()
    if low in COMMON_PASSWORDS or len(set(password)) <= 3:
        problems.append("Bu parol juda keng tarqalgan yoki oddiy")
    local = email.split("@")[0].lower() if email else ""
    if local and len(local) >= 4 and local in low:
        problems.append("Parol elektron pochta nomini o'z ichiga olmasligi kerak")
    for n in names:
        if n and len(n) >= 4 and n.lower() in low and len(low) - len(n) < 6:
            problems.append("Parol ismingizga juda o'xshash")
            break
    return problems


def create_access_token(user_id: uuid.UUID, role: str) -> tuple[str, int]:
    s = get_settings()
    expires = timedelta(minutes=s.ACCESS_TOKEN_MINUTES)
    now = datetime.now(UTC)
    payload = {"sub": str(user_id), "role": role, "type": "access", "iat": now, "exp": now + expires,
               "jti": uuid.uuid4().hex}
    return jwt.encode(payload, s.JWT_SECRET, algorithm=s.JWT_ALGORITHM), int(expires.total_seconds())


def decode_access_token(token: str) -> dict:
    s = get_settings()
    payload = jwt.decode(token, s.JWT_SECRET, algorithms=[s.JWT_ALGORITHM])
    if payload.get("type") != "access":
        raise jwt.InvalidTokenError("wrong token type")
    return payload


def new_opaque_token() -> str:
    return secrets.token_urlsafe(48)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
