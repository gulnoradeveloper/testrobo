"""SQLAlchemy ORM models. Types are portable (PostgreSQL in production, SQLite allowed in tests)."""
import enum
import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    JSON, Boolean, DateTime, Enum, ForeignKey, Index, Integer, String, Text, UniqueConstraint, Uuid,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

JSONType = JSON().with_variant(JSONB(), "postgresql")


def utcnow() -> datetime:
    return datetime.now(UTC)


def _uuid_pk() -> Mapped[uuid.UUID]:
    return mapped_column(Uuid, primary_key=True, default=uuid.uuid4)


def _created() -> Mapped[datetime]:
    return mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class UserRole(str, enum.Enum):
    STUDENT = "student"
    ADMIN = "admin"


class ProjectCategory(str, enum.Enum):
    WEB = "web"
    MOBILE = "mobile"
    INFO_SYSTEM = "info_system"
    AI = "ai"
    CYBERSECURITY = "cybersecurity"
    IOT = "iot"
    ROBOTICS = "robotics"
    OTHER = "other"


class ExtractionStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    EMPTY = "empty"
    FAILED = "failed"


class AnalysisStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class DefenseMode(str, enum.Enum):
    HACKATHON = "hackathon"
    CLIENT = "client"
    ACADEMIC = "academic"
    INVESTOR = "investor"


class SessionStatus(str, enum.Enum):
    CREATED = "CREATED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    EVALUATING = "EVALUATING"
    EVALUATED = "EVALUATED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class JobStatus(str, enum.Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


def _enum(e: type[enum.Enum], name: str):
    return Enum(e, name=name, native_enum=False, length=32, values_callable=lambda x: [m.value for m in x])


class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = _uuid_pk()
    first_name: Mapped[str] = mapped_column(String(80))
    last_name: Mapped[str] = mapped_column(String(80))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    university: Mapped[str] = mapped_column(String(200), default="")
    study_program: Mapped[str] = mapped_column(String(200), default="")
    role: Mapped[UserRole] = mapped_column(_enum(UserRole, "user_role"), default=UserRole.STUDENT)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    ai_consent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Student-granted, time-limited permission for admins to open project content (audited).
    support_access_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = _created()
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class Project(Base):
    __tablename__ = "projects"
    id: Mapped[uuid.UUID] = _uuid_pk()
    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    category: Mapped[ProjectCategory] = mapped_column(_enum(ProjectCategory, "project_category"))
    description: Mapped[str] = mapped_column(Text)
    problem: Mapped[str] = mapped_column(Text)
    objective: Mapped[str] = mapped_column(Text, default="")
    target_users: Mapped[str] = mapped_column(Text, default="")
    features: Mapped[str] = mapped_column(Text, default="")
    technologies: Mapped[str] = mapped_column(Text, default="")
    innovation: Mapped[str] = mapped_column(Text, default="")
    expected_results: Mapped[str] = mapped_column(Text, default="")
    future_plans: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = _created()
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)

    files: Mapped[list["ProjectFile"]] = relationship(back_populates="project", cascade="all, delete-orphan",
                                                      order_by="ProjectFile.created_at")


class ProjectFile(Base):
    __tablename__ = "project_files"
    id: Mapped[uuid.UUID] = _uuid_pk()
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    original_filename: Mapped[str] = mapped_column(String(255))
    storage_key: Mapped[str] = mapped_column(String(255), unique=True)
    mime_type: Mapped[str] = mapped_column(String(120))
    file_size: Mapped[int] = mapped_column(Integer)
    sha256: Mapped[str] = mapped_column(String(64))
    extraction_status: Mapped[ExtractionStatus] = mapped_column(_enum(ExtractionStatus, "extraction_status"))
    extraction_error: Mapped[str | None] = mapped_column(Text)
    extracted_text: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = _created()

    project: Mapped[Project] = relationship(back_populates="files")


class ProjectAnalysis(Base):
    __tablename__ = "project_analyses"
    id: Mapped[uuid.UUID] = _uuid_pk()
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    input_snapshot_hash: Mapped[str] = mapped_column(String(64), index=True)
    ai_model: Mapped[str] = mapped_column(String(100))
    prompt_version: Mapped[str] = mapped_column(String(20))
    result_json: Mapped[dict | None] = mapped_column(JSONType)
    status: Mapped[AnalysisStatus] = mapped_column(_enum(AnalysisStatus, "analysis_status"))
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = _created()


class DefenseSession(Base):
    __tablename__ = "defense_sessions"
    id: Mapped[uuid.UUID] = _uuid_pk()
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    mode: Mapped[DefenseMode] = mapped_column(_enum(DefenseMode, "defense_mode"))
    question_limit: Mapped[int] = mapped_column(Integer)
    status: Mapped[SessionStatus] = mapped_column(_enum(SessionStatus, "session_status"), index=True)
    rubric_version: Mapped[str] = mapped_column(String(20))
    project_snapshot_hash: Mapped[str] = mapped_column(String(64))
    failure_reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = _created()
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    evaluated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    questions: Mapped[list["DefenseQuestion"]] = relationship(
        back_populates="session", cascade="all, delete-orphan", order_by="DefenseQuestion.sequence_number")


class DefenseQuestion(Base):
    __tablename__ = "defense_questions"
    __table_args__ = (UniqueConstraint("session_id", "sequence_number", name="uq_question_seq"),)
    id: Mapped[uuid.UUID] = _uuid_pk()
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("defense_sessions.id", ondelete="CASCADE"), index=True)
    sequence_number: Mapped[int] = mapped_column(Integer)
    question_text: Mapped[str] = mapped_column(Text)
    question_type: Mapped[str] = mapped_column(String(40))  # main | follow_up
    project_reference: Mapped[str | None] = mapped_column(Text)
    focus_area: Mapped[str | None] = mapped_column(String(120))
    created_at: Mapped[datetime] = _created()

    session: Mapped[DefenseSession] = relationship(back_populates="questions")
    answer: Mapped["DefenseAnswer | None"] = relationship(back_populates="question", uselist=False,
                                                          cascade="all, delete-orphan")


class DefenseAnswer(Base):
    __tablename__ = "defense_answers"
    id: Mapped[uuid.UUID] = _uuid_pk()
    question_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("defense_questions.id", ondelete="CASCADE"),
                                                   unique=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    answer_text: Mapped[str] = mapped_column(Text)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    question: Mapped[DefenseQuestion] = relationship(back_populates="answer")
    evaluation: Mapped["AnswerEvaluation | None"] = relationship(back_populates="answer", uselist=False,
                                                                 cascade="all, delete-orphan")


class AnswerEvaluation(Base):
    __tablename__ = "answer_evaluations"
    id: Mapped[uuid.UUID] = _uuid_pk()
    answer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("defense_answers.id", ondelete="CASCADE"), unique=True)
    rubric_version: Mapped[str] = mapped_column(String(20))
    ai_model: Mapped[str] = mapped_column(String(100))
    result_json: Mapped[dict] = mapped_column(JSONType)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    answer: Mapped[DefenseAnswer] = relationship(back_populates="evaluation")


class CompetencyResult(Base):
    __tablename__ = "competency_results"
    id: Mapped[uuid.UUID] = _uuid_pk()
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("defense_sessions.id", ondelete="CASCADE"),
                                                  unique=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    rubric_version: Mapped[str] = mapped_column(String(20))
    total_score: Mapped[float] = mapped_column()
    max_applicable_score: Mapped[int] = mapped_column(Integer)
    coverage: Mapped[float] = mapped_column()
    level: Mapped[str] = mapped_column(String(40))
    criteria_json: Mapped[list] = mapped_column(JSONType)
    readiness_json: Mapped[dict] = mapped_column(JSONType)
    summary_json: Mapped[dict] = mapped_column(JSONType)
    created_at: Mapped[datetime] = _created()


class ImprovementPlan(Base):
    __tablename__ = "improvement_plans"
    id: Mapped[uuid.UUID] = _uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("defense_sessions.id", ondelete="CASCADE"),
                                                  unique=True)
    target_competencies: Mapped[list] = mapped_column(JSONType)
    recommendations_json: Mapped[dict] = mapped_column(JSONType)
    status: Mapped[str] = mapped_column(String(20), default="active")  # active | completed
    created_at: Mapped[datetime] = _created()


class PracticeAttempt(Base):
    __tablename__ = "practice_attempts"
    id: Mapped[uuid.UUID] = _uuid_pk()
    plan_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("improvement_plans.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    exercise_index: Mapped[int] = mapped_column(Integer)
    target_competency: Mapped[str] = mapped_column(String(8))
    original_answer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("defense_answers.id", ondelete="CASCADE"))
    revised_answer: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending | evaluated | failed
    evaluation_json: Mapped[dict | None] = mapped_column(JSONType)
    created_at: Mapped[datetime] = _created()


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    id: Mapped[uuid.UUID] = _uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    family_id: Mapped[uuid.UUID] = mapped_column(Uuid, index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = _created()


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"
    id: Mapped[uuid.UUID] = _uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = _created()


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (Index("ix_audit_actor_created", "actor_id", "created_at"),)
    id: Mapped[uuid.UUID] = _uuid_pk()
    actor_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    action: Mapped[str] = mapped_column(String(80))
    resource_type: Mapped[str] = mapped_column(String(60))
    resource_id: Mapped[str | None] = mapped_column(String(64))
    details: Mapped[dict | None] = mapped_column(JSONType)
    created_at: Mapped[datetime] = _created()


class AIJob(Base):
    __tablename__ = "ai_jobs"
    id: Mapped[uuid.UUID] = _uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(40))
    resource_type: Mapped[str] = mapped_column(String(40))
    resource_id: Mapped[uuid.UUID] = mapped_column(Uuid, index=True)
    payload: Mapped[dict | None] = mapped_column(JSONType)
    status: Mapped[JobStatus] = mapped_column(_enum(JobStatus, "job_status"), index=True)
    error_code: Mapped[str | None] = mapped_column(String(60))
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = _created()
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class AIRequestLog(Base):
    """Technical monitoring only: never stores prompt or response content."""
    __tablename__ = "ai_request_logs"
    id: Mapped[uuid.UUID] = _uuid_pk()
    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    operation: Mapped[str] = mapped_column(String(60))
    provider: Mapped[str] = mapped_column(String(40))
    model: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(30))
    latency_ms: Mapped[int] = mapped_column(Integer)
    input_tokens: Mapped[int | None] = mapped_column(Integer)
    output_tokens: Mapped[int | None] = mapped_column(Integer)
    error_type: Mapped[str | None] = mapped_column(String(80))
    created_at: Mapped[datetime] = _created()


class IdempotencyRecord(Base):
    __tablename__ = "idempotency_records"
    __table_args__ = (UniqueConstraint("user_id", "key", "endpoint", name="uq_idempotency"),)
    id: Mapped[uuid.UUID] = _uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    key: Mapped[str] = mapped_column(String(100))
    endpoint: Mapped[str] = mapped_column(String(200))
    status_code: Mapped[int] = mapped_column(Integer)
    response_json: Mapped[dict] = mapped_column(JSONType)
    created_at: Mapped[datetime] = _created()


class SystemSetting(Base):
    __tablename__ = "system_settings"
    key: Mapped[str] = mapped_column(String(80), primary_key=True)
    value: Mapped[dict] = mapped_column(JSONType)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
