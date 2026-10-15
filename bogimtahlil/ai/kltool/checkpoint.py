"""Checkpoint formati, SHA-256 va moslik tekshiruvi.

Checkpoint `torch.save` bilan saqlanadigan lug‘at:
    format_version, architecture, class_names, preprocess, model_version,
    training_status ("trained" | "untrained-test-fixture"), dataset, metrics, training, state_dict

Yuklash `torch.load(weights_only=True)` bilan bajariladi — ixtiyoriy Python obyektlari
(pickle orqali kod bajarish) rad etiladi.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import torch
import torch.nn as nn

from . import KL_CLASSES
from .architectures import SUPPORTED_ARCHITECTURES, build_model
from .preprocess import PREPROCESS_VERSION, PreprocessConfig

CHECKPOINT_FORMAT_VERSION = 1
TRAINED = "trained"
UNTRAINED_FIXTURE = "untrained-test-fixture"


class CheckpointError(Exception):
    """Checkpoint yo‘q, buzilgan yoki dastur bilan mos emas."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass
class LoadedModel:
    model: nn.Module
    architecture: str
    class_names: list[str]
    preprocess: PreprocessConfig
    model_version: str
    training_status: str
    sha256: str
    dataset: dict[str, Any] = field(default_factory=dict)
    metrics: dict[str, Any] = field(default_factory=dict)
    training: dict[str, Any] = field(default_factory=dict)
    path: str = ""


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def save_checkpoint(
    path: str | Path,
    model: nn.Module,
    architecture: str,
    model_version: str,
    preprocess: PreprocessConfig,
    training_status: str = TRAINED,
    dataset: dict | None = None,
    metrics: dict | None = None,
    training: dict | None = None,
) -> str:
    payload = {
        "format_version": CHECKPOINT_FORMAT_VERSION,
        "architecture": architecture,
        "class_names": list(KL_CLASSES),
        "preprocess": preprocess.to_dict(),
        "model_version": model_version,
        "training_status": training_status,
        "dataset": dataset or {},
        "metrics": metrics or {},
        "training": training or {},
        "state_dict": {k: v.detach().cpu() for k, v in model.state_dict().items()},
    }
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(payload, path)
    digest = sha256_file(path)
    path.with_suffix(path.suffix + ".sha256").write_text(f"{digest}  {path.name}\n", encoding="utf-8")
    return digest


def load_checkpoint(
    path: str | Path,
    device: str | torch.device = "cpu",
    expected_sha256: str | None = None,
    allow_untrained: bool = False,
) -> LoadedModel:
    path = Path(path)
    if not path.is_file():
        raise CheckpointError("MODEL_NOT_FOUND", f"Model fayli topilmadi: {path.name}")

    digest = sha256_file(path)
    if expected_sha256 and digest.lower() != expected_sha256.strip().lower():
        raise CheckpointError("MODEL_HASH_MISMATCH", "Model faylining SHA-256 qiymati kutilgan qiymatga mos emas")

    try:
        payload = torch.load(path, map_location="cpu", weights_only=True)
    except Exception as exc:  # buzilgan yoki xavfli pickle
        raise CheckpointError("MODEL_CORRUPTED", f"Checkpointni o‘qib bo‘lmadi: {type(exc).__name__}") from exc

    if not isinstance(payload, dict) or "state_dict" not in payload:
        raise CheckpointError("MODEL_INCOMPATIBLE", "Checkpoint formati noma’lum")
    if payload.get("format_version") != CHECKPOINT_FORMAT_VERSION:
        raise CheckpointError("MODEL_INCOMPATIBLE", f"Checkpoint format versiyasi mos emas: {payload.get('format_version')}")

    arch = payload.get("architecture")
    if arch not in SUPPORTED_ARCHITECTURES:
        raise CheckpointError("MODEL_INCOMPATIBLE", f"Noma’lum arxitektura: {arch}")

    class_names = list(payload.get("class_names") or [])
    if class_names != list(KL_CLASSES):
        raise CheckpointError("MODEL_INCOMPATIBLE", f"Sinflar tartibi mos emas: {class_names}")

    try:
        pp = PreprocessConfig.from_dict(payload["preprocess"])
    except Exception as exc:
        raise CheckpointError("MODEL_INCOMPATIBLE", "Preprocess konfiguratsiyasi checkpointda yo‘q yoki buzilgan") from exc
    if pp.version != PREPROCESS_VERSION:
        raise CheckpointError(
            "MODEL_INCOMPATIBLE",
            f"Preprocess versiyasi mos emas: checkpoint={pp.version}, dastur={PREPROCESS_VERSION}",
        )

    status = payload.get("training_status")
    if status != TRAINED and not allow_untrained:
        raise CheckpointError(
            "MODEL_NOT_TRAINED",
            "Checkpoint o‘qitilgan model sifatida belgilanmagan — real tahlil uchun ishlatilmaydi",
        )

    model = build_model(arch, num_classes=len(class_names), pretrained=False)
    try:
        model.load_state_dict(payload["state_dict"], strict=True)
    except RuntimeError as exc:
        raise CheckpointError("MODEL_INCOMPATIBLE", "Vaznlar arxitekturaga mos kelmadi") from exc

    model.to(device).eval()
    return LoadedModel(
        model=model,
        architecture=arch,
        class_names=class_names,
        preprocess=pp,
        model_version=str(payload.get("model_version") or "noma’lum"),
        training_status=str(status),
        sha256=digest,
        dataset=dict(payload.get("dataset") or {}),
        metrics=dict(payload.get("metrics") or {}),
        training=dict(payload.get("training") or {}),
        path=str(path),
    )
