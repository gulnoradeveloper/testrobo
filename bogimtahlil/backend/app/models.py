"""Ma’lumotlar bazasi jadvallari: analyses, model_versions, artifacts.

Bemorning ismi, telefoni, pasporti va asl fayl nomi saqlanmaydi.
session_id — brauzer cookie tokenining SHA-256 qiymati (tokenning o‘zi bazada yo‘q).
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Analysis(Base):
    __tablename__ = "analyses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    session_id: Mapped[str] = mapped_column(String(64), index=True)
    image_hash: Mapped[str] = mapped_column(String(64))
    predicted_class: Mapped[int | None] = mapped_column(Integer, nullable=True)
    probabilities_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    model_version: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(20))  # completed | failed
    processing_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    timing_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_width: Mapped[int] = mapped_column(Integer)
    image_height: Mapped[int] = mapped_column(Integer)
    error_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    model_version_id: Mapped[int | None] = mapped_column(ForeignKey("model_versions.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)

    artifacts: Mapped[list["Artifact"]] = relationship(back_populates="analysis", cascade="all, delete-orphan")
    model: Mapped["ModelVersion | None"] = relationship()


class ModelVersion(Base):
    __tablename__ = "model_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    model_name: Mapped[str] = mapped_column(String(200))
    version: Mapped[str] = mapped_column(String(100))
    architecture: Mapped[str] = mapped_column(String(50))
    checkpoint_hash: Mapped[str] = mapped_column(String(64), unique=True)
    preprocess_version: Mapped[str] = mapped_column(String(20))
    class_names: Mapped[str] = mapped_column(Text)
    training_status: Mapped[str] = mapped_column(String(40))
    metrics_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Artifact(Base):
    __tablename__ = "artifacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    analysis_id: Mapped[str] = mapped_column(ForeignKey("analyses.id", ondelete="CASCADE"), index=True)
    artifact_type: Mapped[str] = mapped_column(String(20))  # original | heatmap | overlay | report
    file_path: Mapped[str] = mapped_column(String(500))  # storage_dir ga nisbatan
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    analysis: Mapped[Analysis] = relationship(back_populates="artifacts")
