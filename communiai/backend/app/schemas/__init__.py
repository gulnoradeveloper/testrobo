"""Request/response schemas for the REST API."""
import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models import DefenseMode, ProjectCategory


def _strip(v):
    return v.strip() if isinstance(v, str) else v


class RegisterIn(BaseModel):
    first_name: str = Field(min_length=1, max_length=80)
    last_name: str = Field(min_length=1, max_length=80)
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)
    password_confirm: str = Field(min_length=1, max_length=128)
    university: str = Field(min_length=2, max_length=200)
    study_program: str = Field(min_length=2, max_length=200)

    _s = field_validator("first_name", "last_name", "university", "study_program", mode="before")(_strip)


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class RefreshIn(BaseModel):
    refresh_token: str = Field(min_length=10, max_length=200)


class PasswordResetRequestIn(BaseModel):
    email: EmailStr


class PasswordResetConfirmIn(BaseModel):
    token: str = Field(min_length=10, max_length=200)
    new_password: str = Field(min_length=1, max_length=128)
    new_password_confirm: str = Field(min_length=1, max_length=128)


class ChangePasswordIn(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=1, max_length=128)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    first_name: str
    last_name: str
    email: str
    university: str
    study_program: str
    role: str
    ai_consent_at: datetime | None
    support_access_until: datetime | None
    created_at: datetime

    @field_validator("role", mode="before")
    @classmethod
    def _role(cls, v):
        return v.value if hasattr(v, "value") else v


class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserOut


class ProfileUpdateIn(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=80)
    last_name: str | None = Field(default=None, min_length=1, max_length=80)
    university: str | None = Field(default=None, min_length=2, max_length=200)
    study_program: str | None = Field(default=None, min_length=2, max_length=200)
    ai_consent: bool | None = None
    support_access_days: int | None = Field(default=None, ge=0, le=30)

    _s = field_validator("first_name", "last_name", "university", "study_program", mode="before")(_strip)


TEXT = 5000


class ProjectBase(BaseModel):
    objective: str = Field(default="", max_length=TEXT)
    target_users: str = Field(default="", max_length=TEXT)
    features: str = Field(default="", max_length=TEXT)
    technologies: str = Field(default="", max_length=TEXT)
    innovation: str = Field(default="", max_length=TEXT)
    expected_results: str = Field(default="", max_length=TEXT)
    future_plans: str = Field(default="", max_length=TEXT)


class ProjectCreate(ProjectBase):
    title: str = Field(min_length=3, max_length=200)
    category: ProjectCategory
    description: str = Field(min_length=20, max_length=10000)
    problem: str = Field(min_length=10, max_length=TEXT)

    _s = field_validator("title", "description", "problem", mode="before")(_strip)


class ProjectUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=200)
    category: ProjectCategory | None = None
    description: str | None = Field(default=None, min_length=20, max_length=10000)
    problem: str | None = Field(default=None, min_length=10, max_length=TEXT)
    objective: str | None = Field(default=None, max_length=TEXT)
    target_users: str | None = Field(default=None, max_length=TEXT)
    features: str | None = Field(default=None, max_length=TEXT)
    technologies: str | None = Field(default=None, max_length=TEXT)
    innovation: str | None = Field(default=None, max_length=TEXT)
    expected_results: str | None = Field(default=None, max_length=TEXT)
    future_plans: str | None = Field(default=None, max_length=TEXT)

    _s = field_validator("title", "description", "problem", mode="before")(_strip)


class DefenseCreate(BaseModel):
    project_id: uuid.UUID
    mode: DefenseMode
    question_limit: Literal[5, 10, 15] = 10


class AnswerIn(BaseModel):
    question_id: uuid.UUID
    answer_text: str = Field(min_length=1, max_length=6000)

    @field_validator("answer_text")
    @classmethod
    def _not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Javob bo'sh bo'lmasligi kerak")
        return v.strip()


class PracticePlanCreate(BaseModel):
    session_id: uuid.UUID


class PracticeAttemptIn(BaseModel):
    exercise_index: int = Field(ge=0, le=10)
    revised_answer: str = Field(min_length=1, max_length=6000)

    @field_validator("revised_answer")
    @classmethod
    def _not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Javob bo'sh bo'lmasligi kerak")
        return v.strip()


class AdminSettingIn(BaseModel):
    key: str
    value: bool | str


class AdminProjectAccessIn(BaseModel):
    reason: str = Field(min_length=10, max_length=500)
