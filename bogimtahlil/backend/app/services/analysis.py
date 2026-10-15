"""Tahlil biznes-mantiqi: validatsiya → model → saqlash → javob shakllantirish."""
from __future__ import annotations

import hashlib
import json
import logging
import time
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from kltool import KL_CLASSES
from kltool.architectures import DISPLAY_NAMES
from kltool.gradcam import overlay as make_overlay

from ..config import Settings
from ..errors import ApiError
from ..messages import (DISCLAIMER, GRADCAM_NOTE, KL_REFERENCE, KL_SOURCE, LIMITATIONS, PROBABILITY_NOTE,
                        SPECIALIST_ADVICE)
from ..models import Analysis, Artifact, ModelVersion
from ..schemas import AnalysisListItem, AnalysisOut
from .inference import ModelService
from .storage import Storage
from .validation import ValidatedImage

log = logging.getLogger("bogimtahlil.analysis")
API = "/api/v1/analyses"
GRADCAM_ERRORS = {
    "GRADCAM_FAILED": "Faollik xaritasini yaratishda xatolik yuz berdi.",
    "GRADCAM_EMPTY": "Faollik xaritasi bo‘sh: model ushbu bashorat uchun ajralib turadigan sohani ko‘rsatmadi.",
}


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def analysis_number(a: Analysis) -> str:
    return f"BT-{_aware(a.created_at):%Y%m%d}-{a.id[:6].upper()}"


def heatmap_rgba(cam):
    """Frontendda shaffoflik bilan ustma-ust qo‘yish uchun RGBA: alfa = faollik darajasi."""
    import numpy as np

    from kltool.gradcam import colorize

    rgb = colorize(cam)
    alpha = (np.clip(cam, 0, 1) * 255).astype(np.uint8)[:, :, None]
    return np.concatenate([rgb, alpha], axis=2)


def register_model_version(db: Session, svc: ModelService, settings: Settings) -> ModelVersion | None:
    lm = svc.loaded
    if lm is None:
        return None
    mv = db.scalar(select(ModelVersion).where(ModelVersion.checkpoint_hash == lm.sha256))
    if mv is None:
        mv = ModelVersion(
            model_name=settings.model_name, version=lm.model_version, architecture=lm.architecture,
            checkpoint_hash=lm.sha256, preprocess_version=lm.preprocess.version,
            class_names=json.dumps(lm.class_names), training_status=lm.training_status,
            metrics_json=json.dumps(lm.metrics, ensure_ascii=False), created_at=utcnow(),
        )
        db.add(mv)
        db.commit()
    return mv


def run_analysis(db: Session, svc: ModelService, storage: Storage, settings: Settings, session_id: str,
                 img: ValidatedImage, raw: bytes) -> Analysis:
    lm = svc.require()
    started = time.perf_counter()
    analysis_id = str(uuid.uuid4())
    try:
        pred = svc.predict(img.gray)
    except ApiError:
        raise
    except Exception:
        log.exception("Inference xatosi")
        raise ApiError("ANALYSIS_FAILED", 500) from None

    now = utcnow()
    expires = now + timedelta(hours=settings.retention_hours)
    mv = register_model_version(db, svc, settings)
    a = Analysis(
        id=analysis_id, session_id=session_id, image_hash=hashlib.sha256(raw).hexdigest(),
        predicted_class=pred.predicted_class, probabilities_json=json.dumps(pred.probabilities),
        model_version=lm.model_version, status="completed", image_width=img.width, image_height=img.height,
        error_code=pred.gradcam_error,
        model_version_id=mv.id if mv else None, created_at=now, expires_at=expires,
    )
    try:
        files = [("original", storage.save_png(analysis_id, "original", img.gray))]
        if pred.cam is not None:
            files.append(("heatmap", storage.save_png(analysis_id, "heatmap", heatmap_rgba(pred.cam))))
            files.append(("overlay", storage.save_png(analysis_id, "overlay", make_overlay(img.gray, pred.cam))))
        pred.timing_ms["total_ms"] = (time.perf_counter() - started) * 1000
        a.timing_json = json.dumps({k: round(v, 1) for k, v in pred.timing_ms.items()})
        a.processing_time_ms = int(round(pred.timing_ms["total_ms"]))
        db.add(a)
        for t, rel in files:
            db.add(Artifact(analysis_id=analysis_id, artifact_type=t, file_path=rel, created_at=now, expires_at=expires))
        db.commit()
    except Exception:
        db.rollback()
        storage.delete_analysis(analysis_id)
        log.exception("Natijani saqlashda xatolik")
        raise ApiError("ANALYSIS_FAILED", 500) from None
    return a


def get_owned(db: Session, analysis_id: str, session_id: str) -> Analysis:
    try:
        uuid.UUID(analysis_id)
    except ValueError:
        raise ApiError("NOT_FOUND", 404) from None
    a = db.get(Analysis, analysis_id)
    if a is None or _aware(a.expires_at) <= utcnow():
        raise ApiError("NOT_FOUND", 404)
    if a.session_id != session_id:
        raise ApiError("FORBIDDEN", 403)
    return a


def artifact_path(a: Analysis, artifact_type: str) -> str | None:
    for art in a.artifacts:
        if art.artifact_type == artifact_type:
            return art.file_path
    return None


def to_out(a: Analysis, settings: Settings) -> AnalysisOut:
    probs = json.loads(a.probabilities_json or "[]")
    k = int(a.predicted_class)
    mv = a.model
    has_heat = artifact_path(a, "heatmap") is not None
    base = f"{API}/{a.id}"
    return AnalysisOut(
        id=a.id, number=analysis_number(a), status=a.status, created_at=_aware(a.created_at),
        expires_at=_aware(a.expires_at),
        model={
            "name": mv.model_name if mv else settings.model_name,
            "version": a.model_version,
            "architecture": DISPLAY_NAMES.get(mv.architecture, mv.architecture) if mv else "noma’lum",
            "checkpoint_sha256": mv.checkpoint_hash if mv else "",
            "training_status": mv.training_status if mv else "noma’lum",
        },
        prediction={"kl_grade": k, "label": KL_CLASSES[k], "title": KL_REFERENCE[k]["title"],
                    "description": KL_REFERENCE[k]["description"], "reference": KL_SOURCE},
        probabilities=[{"grade": i, "label": KL_CLASSES[i], "title": KL_REFERENCE[i]["title"], "probability": p}
                       for i, p in enumerate(probs)],
        timing=json.loads(a.timing_json or "{}"), processing_time_ms=a.processing_time_ms or 0,
        image={"image_id": a.image_hash[:12], "width": a.image_width, "height": a.image_height, "url": f"{base}/image"},
        heatmap={"available": has_heat, "heatmap_url": f"{base}/heatmap?variant=heatmap" if has_heat else None,
                 "overlay_url": f"{base}/heatmap?variant=overlay" if has_heat else None, "note": GRADCAM_NOTE,
                 "error": GRADCAM_ERRORS.get(a.error_code or "")},
        report_url=f"{base}/report", disclaimer=DISCLAIMER, probability_note=PROBABILITY_NOTE,
        limitations=LIMITATIONS, specialist_advice=SPECIALIST_ADVICE,
    )


def to_list_item(a: Analysis) -> AnalysisListItem:
    k = int(a.predicted_class)
    return AnalysisListItem(
        id=a.id, number=analysis_number(a), created_at=_aware(a.created_at), expires_at=_aware(a.expires_at),
        image_id=a.image_hash[:12], kl_grade=k, label=KL_CLASSES[k], title=KL_REFERENCE[k]["title"],
        model_version=a.model_version, report_url=f"{API}/{a.id}/report",
    )


def delete_analysis(db: Session, storage: Storage, a: Analysis) -> None:
    aid = a.id
    db.delete(a)
    db.commit()
    storage.delete_analysis(aid)


def purge_expired(db: Session, storage: Storage) -> int:
    now = utcnow()
    ids = list(db.scalars(select(Analysis.id).where(Analysis.expires_at <= now)))
    if ids:
        db.execute(delete(Artifact).where(Artifact.analysis_id.in_(ids)))
        db.execute(delete(Analysis).where(Analysis.id.in_(ids)))
        db.commit()
    for aid in ids:
        storage.delete_analysis(aid)
    # Bazada yozuvi yo‘q yetim kataloglarni ham tozalash
    known = set(db.scalars(select(Analysis.id)))
    cutoff = time.time() - 600  # hozir yozilayotgan tahlillarga tegmaslik uchun
    for d in storage.root.iterdir():
        if d.is_dir() and d.name not in known and d.stat().st_mtime < cutoff:
            storage.delete_analysis(d.name)
    return len(ids)
