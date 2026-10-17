"""REST API: /api/v1/..."""
from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, File, Form, Query, Request, Response, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from kltool import KL_CLASSES

from .. import __version__
from ..config import Settings
from ..errors import ApiError
from ..messages import KL_REFERENCE, LIMITATIONS
from ..models import Analysis, Artifact
from ..schemas import AnalysisList, AnalysisOut, HealthOut, ModelInfoOut
from ..services import analysis as svc_analysis
from ..services.inference import ModelService
from ..services.report import build_report
from ..services.storage import Storage
from ..services.validation import validate_upload
from ..session import get_or_create_session

router = APIRouter(prefix="/api/v1")

MODEL_NOT_READY_UI = "Sun’iy intellekt modeli hozircha tahlil qilish uchun tayyor emas."


def get_settings_dep(request: Request) -> Settings:
    return request.app.state.settings


def get_db(request: Request):
    db = request.app.state.session_factory()
    try:
        yield db
    finally:
        db.close()


def get_model(request: Request) -> ModelService:
    return request.app.state.model_service


def get_storage(request: Request) -> Storage:
    return request.app.state.storage


def session_id_dep(request: Request, response: Response, settings: Settings = Depends(get_settings_dep)) -> str:
    return get_or_create_session(request, response, settings)


def _model_status_message(m: ModelService) -> str:
    if m.ready and m.is_trained:
        return "Model yuklangan va tahlilga tayyor."
    if m.ready:
        return "Yuklangan checkpoint o‘qitilgan model emas (faqat test rejimi) — natijalar ma’noga ega emas."
    if m.error_code == "MODEL_NOT_FOUND":
        return "Model hali o‘qitilmagan: artifacts/model.pt mavjud emas."
    return MODEL_NOT_READY_UI


@router.get("/health", response_model=HealthOut)
def health(db: Session = Depends(get_db), m: ModelService = Depends(get_model)):
    try:
        db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception:
        db_status = "xato"
    return HealthOut(
        status="ok" if db_status == "ok" else "degraded", version=__version__, database=db_status,
        model_loaded=m.ready, model_trained=m.is_trained, model_status_message=_model_status_message(m),
        device=str(m.device),
    )


@router.get("/model/info", response_model=ModelInfoOut)
def model_info(m: ModelService = Depends(get_model), settings: Settings = Depends(get_settings_dep)):
    lm = m.loaded
    metrics = dict(lm.metrics) if lm else {}
    return ModelInfoOut(
        loaded=m.ready, trained=m.is_trained, status_code=m.error_code, status_message=_model_status_message(m),
        name=settings.model_name, architecture=m.display_architecture, version=lm.model_version if lm else None,
        checkpoint_sha256=lm.sha256 if lm else None, preprocess=lm.preprocess.to_dict() if lm else None,
        class_names=list(KL_CLASSES), class_titles={KL_CLASSES[k]: v["title"] for k, v in KL_REFERENCE.items()},
        dataset=lm.dataset if lm else {}, metrics=metrics,
        training={k: v for k, v in (lm.training if lm else {}).items() if k not in ("manifest", "output_dir")},
        calibration_evaluated=bool(metrics.get("calibration_evaluated", False)), limitations=LIMITATIONS,
    )


@router.get("/model/experiments")
def model_experiments(m: ModelService = Depends(get_model), settings: Settings = Depends(get_settings_dep)):
    """Ma’lumotlar to‘plami, o‘qitish grafiklari, modellarni taqqoslash va test natijalari (faqat fayllardan)."""
    from ..services.experiments import collect

    lm = m.loaded
    return collect(settings.experiments_dir, settings.splits_dir, lm.metrics if lm else None, lm.dataset if lm else None)


@router.post("/analyses", response_model=AnalysisOut, status_code=201)
async def create_analysis(
    request: Request,
    file: UploadFile | None = File(default=None),
    projection_confirmed: bool = Form(default=False),
    session_id: str = Depends(session_id_dep),
    db: Session = Depends(get_db),
    m: ModelService = Depends(get_model),
    storage: Storage = Depends(get_storage),
    settings: Settings = Depends(get_settings_dep),
):
    if file is None or not file.filename:
        raise ApiError("NO_FILE", 400)
    # Hajm chegarasidan +1 bayt o‘qiladi — butun faylni xotiraga cheksiz yuklamaslik uchun
    raw = await file.read(settings.max_upload_bytes + 1)
    await file.close()
    if len(raw) > settings.max_upload_bytes:
        raise ApiError("FILE_TOO_LARGE", 413)
    img = await run_in_threadpool(
        validate_upload, raw, file.filename, file.content_type, settings.max_upload_bytes,
        settings.max_image_pixels, settings.min_image_side,
    )
    if not projection_confirmed:
        raise ApiError("PROJECTION_NOT_CONFIRMED", 422)
    if not m.ready:
        raise ApiError("MODEL_NOT_READY", 503, details={"reason": m.error_code, "ui_message": MODEL_NOT_READY_UI})
    a = await run_in_threadpool(svc_analysis.run_analysis, db, m, storage, settings, session_id, img, raw)
    db.refresh(a)
    return svc_analysis.to_out(a, settings)


@router.get("/analyses", response_model=AnalysisList)
def list_analyses(
    session_id: str = Depends(session_id_dep),
    db: Session = Depends(get_db),
    grade: int | None = Query(default=None, ge=0, le=4),
    sort: Literal["newest", "oldest", "grade_asc", "grade_desc"] = "newest",
):
    q = select(Analysis).where(Analysis.session_id == session_id, Analysis.status == "completed",
                               Analysis.expires_at > svc_analysis.utcnow())
    if grade is not None:
        q = q.where(Analysis.predicted_class == grade)
    order = {
        "newest": [Analysis.created_at.desc()], "oldest": [Analysis.created_at.asc()],
        "grade_asc": [Analysis.predicted_class.asc(), Analysis.created_at.desc()],
        "grade_desc": [Analysis.predicted_class.desc(), Analysis.created_at.desc()],
    }[sort]
    items = [svc_analysis.to_list_item(a) for a in db.scalars(q.order_by(*order))]
    return AnalysisList(items=items, total=len(items))


@router.get("/analyses/{analysis_id}", response_model=AnalysisOut)
def get_analysis(analysis_id: str, session_id: str = Depends(session_id_dep), db: Session = Depends(get_db),
                 settings: Settings = Depends(get_settings_dep)):
    return svc_analysis.to_out(svc_analysis.get_owned(db, analysis_id, session_id), settings)


def _file(storage: Storage, rel: str | None, media: str, download_name: str | None = None) -> FileResponse:
    if rel is None:
        raise ApiError("NOT_FOUND", 404)
    p = storage.abspath(rel)
    if not p.is_file():
        raise ApiError("NOT_FOUND", 404)
    headers = {"Cache-Control": "private, no-store"}
    if download_name:
        return FileResponse(p, media_type=media, filename=download_name, headers=headers)
    return FileResponse(p, media_type=media, headers=headers)


@router.get("/analyses/{analysis_id}/image")
def get_image(analysis_id: str, session_id: str = Depends(session_id_dep), db: Session = Depends(get_db),
              storage: Storage = Depends(get_storage)):
    a = svc_analysis.get_owned(db, analysis_id, session_id)
    return _file(storage, svc_analysis.artifact_path(a, "original"), "image/png")


@router.get("/analyses/{analysis_id}/heatmap")
def get_heatmap(analysis_id: str, variant: Literal["heatmap", "overlay"] = "overlay",
                session_id: str = Depends(session_id_dep), db: Session = Depends(get_db),
                storage: Storage = Depends(get_storage)):
    a = svc_analysis.get_owned(db, analysis_id, session_id)
    rel = svc_analysis.artifact_path(a, variant)
    if rel is None:
        if a.error_code in svc_analysis.GRADCAM_ERRORS:
            raise ApiError(a.error_code, 404, message=svc_analysis.GRADCAM_ERRORS[a.error_code])
        raise ApiError("NOT_FOUND", 404)
    return _file(storage, rel, "image/png")


@router.get("/analyses/{analysis_id}/report")
async def get_report(analysis_id: str, session_id: str = Depends(session_id_dep), db: Session = Depends(get_db),
                     storage: Storage = Depends(get_storage), settings: Settings = Depends(get_settings_dep)):
    a = svc_analysis.get_owned(db, analysis_id, session_id)
    rel = svc_analysis.artifact_path(a, "report")
    name = f"bogimtahlil-{svc_analysis.analysis_number(a)}.pdf"
    if rel is None:
        out = svc_analysis.to_out(a, settings).model_dump(mode="json")
        overlay = svc_analysis.artifact_path(a, "overlay")
        try:
            pdf = await run_in_threadpool(build_report, out, storage.abspath(svc_analysis.artifact_path(a, "original")),
                                          storage.abspath(overlay) if overlay else None)
        except Exception:
            svc_analysis.log.exception("PDF yaratish xatosi")
            raise ApiError("REPORT_FAILED", 500) from None
        rel = storage.save_bytes(a.id, "report", pdf)
        db.add(Artifact(analysis_id=a.id, artifact_type="report", file_path=rel, created_at=svc_analysis.utcnow(),
                        expires_at=a.expires_at))
        db.commit()
    return _file(storage, rel, "application/pdf", name)


@router.delete("/analyses/{analysis_id}", status_code=204)
def delete_analysis(analysis_id: str, session_id: str = Depends(session_id_dep), db: Session = Depends(get_db),
                    storage: Storage = Depends(get_storage)):
    a = svc_analysis.get_owned(db, analysis_id, session_id)
    svc_analysis.delete_analysis(db, storage, a)
    return Response(status_code=204)
