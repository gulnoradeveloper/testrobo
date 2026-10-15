"""Boshlang‘ich sxema: analyses, model_versions, artifacts

Revision ID: 0001_initial
Revises:
Create Date: 2026-10-15
"""
import sqlalchemy as sa
from alembic import op

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "model_versions",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("model_name", sa.String(200), nullable=False),
        sa.Column("version", sa.String(100), nullable=False),
        sa.Column("architecture", sa.String(50), nullable=False),
        sa.Column("checkpoint_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("preprocess_version", sa.String(20), nullable=False),
        sa.Column("class_names", sa.Text, nullable=False),
        sa.Column("training_status", sa.String(40), nullable=False),
        sa.Column("metrics_json", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "analyses",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("session_id", sa.String(64), nullable=False, index=True),
        sa.Column("image_hash", sa.String(64), nullable=False),
        sa.Column("predicted_class", sa.Integer, nullable=True),
        sa.Column("probabilities_json", sa.Text, nullable=True),
        sa.Column("model_version", sa.String(100), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("processing_time_ms", sa.Integer, nullable=True),
        sa.Column("timing_json", sa.Text, nullable=True),
        sa.Column("image_width", sa.Integer, nullable=False),
        sa.Column("image_height", sa.Integer, nullable=False),
        sa.Column("error_code", sa.String(50), nullable=True),
        sa.Column("model_version_id", sa.Integer, sa.ForeignKey("model_versions.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False, index=True),
    )
    op.create_table(
        "artifacts",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("analysis_id", sa.String(36), sa.ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("artifact_type", sa.String(20), nullable=False),
        sa.Column("file_path", sa.String(500), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("artifacts")
    op.drop_table("analyses")
    op.drop_table("model_versions")
