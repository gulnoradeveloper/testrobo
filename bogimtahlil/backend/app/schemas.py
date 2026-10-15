"""API javoblari sxemalari (Pydantic)."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class ModelRef(BaseModel):
    name: str
    version: str
    architecture: str
    checkpoint_sha256: str
    training_status: str


class PredictionOut(BaseModel):
    kl_grade: int
    label: str
    title: str
    description: str
    reference: str


class ProbabilityOut(BaseModel):
    grade: int
    label: str
    title: str
    probability: float


class ImageOut(BaseModel):
    image_id: str
    width: int
    height: int
    url: str


class HeatmapOut(BaseModel):
    available: bool
    heatmap_url: str | None
    overlay_url: str | None
    note: str
    error: str | None = None


class AnalysisOut(BaseModel):
    id: str
    number: str
    status: str
    created_at: datetime
    expires_at: datetime
    model: ModelRef
    prediction: PredictionOut
    probabilities: list[ProbabilityOut]
    timing: dict[str, float]
    processing_time_ms: int
    image: ImageOut
    heatmap: HeatmapOut
    report_url: str
    disclaimer: str
    probability_note: str
    limitations: list[str]
    specialist_advice: str


class AnalysisListItem(BaseModel):
    id: str
    number: str
    created_at: datetime
    expires_at: datetime
    image_id: str
    kl_grade: int
    label: str
    title: str
    model_version: str
    report_url: str


class AnalysisList(BaseModel):
    items: list[AnalysisListItem]
    total: int


class HealthOut(BaseModel):
    status: str
    version: str
    database: str
    model_loaded: bool
    model_trained: bool
    model_status_message: str
    device: str


class ModelInfoOut(BaseModel):
    loaded: bool
    trained: bool
    status_code: str | None
    status_message: str
    name: str
    architecture: str | None
    version: str | None
    checkpoint_sha256: str | None
    preprocess: dict[str, Any] | None
    class_names: list[str]
    class_titles: dict[str, str]
    dataset: dict[str, Any]
    metrics: dict[str, Any]
    training: dict[str, Any]
    calibration_evaluated: bool
    limitations: list[str]
