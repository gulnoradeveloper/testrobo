"""Tracked asynchronous AI jobs.

Long AI operations are recorded in `ai_jobs` and executed on a small thread pool. Clients poll
GET /api/v1/jobs/{id}. Only one active job per resource+kind group is allowed, so repeated taps
never create duplicate (and duplicate-cost) AI work.
"""
import logging
import uuid
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.models import AIJob, JobStatus, utcnow
from app.services.ai.provider import AIError

log = logging.getLogger("communiai.jobs")

Handler = Callable[[Session, AIJob], None]
FailureHook = Callable[[Session, AIJob, str, str], None]

_handlers: dict[str, Handler] = {}
_failure_hooks: dict[str, FailureHook] = {}
_executor: ThreadPoolExecutor | None = None


def register(kind: str, handler: Handler, on_failure: FailureHook | None = None) -> None:
    _handlers[kind] = handler
    if on_failure:
        _failure_hooks[kind] = on_failure


def _get_executor() -> ThreadPoolExecutor:
    global _executor
    if _executor is None:
        _executor = ThreadPoolExecutor(max_workers=get_settings().JOB_WORKERS, thread_name_prefix="ai-job")
    return _executor


def active_job(db: Session, resource_id: uuid.UUID, kinds: tuple[str, ...]) -> AIJob | None:
    return db.scalars(
        select(AIJob).where(AIJob.resource_id == resource_id, AIJob.kind.in_(kinds),
                            AIJob.status.in_([JobStatus.QUEUED, JobStatus.RUNNING]))
        .order_by(AIJob.created_at.desc())
    ).first()


def create_job(db: Session, *, user_id: uuid.UUID, kind: str, resource_type: str, resource_id: uuid.UUID,
               payload: dict | None = None) -> AIJob:
    job = AIJob(user_id=user_id, kind=kind, resource_type=resource_type, resource_id=resource_id,
                payload=payload or {}, status=JobStatus.QUEUED)
    db.add(job)
    db.flush()
    return job


def dispatch(job_id: uuid.UUID) -> None:
    """Call after the creating transaction has been committed."""
    if get_settings().JOB_EXECUTION == "inline":
        run_job(job_id)
    else:
        _get_executor().submit(run_job, job_id)


def run_job(job_id: uuid.UUID) -> None:
    with SessionLocal() as db:
        # Atomically claim the job.
        claimed = db.execute(
            update(AIJob).where(AIJob.id == job_id, AIJob.status == JobStatus.QUEUED)
            .values(status=JobStatus.RUNNING, updated_at=utcnow())
        ).rowcount
        db.commit()
        if not claimed:
            return
        job = db.get(AIJob, job_id)
        handler = _handlers.get(job.kind)
        try:
            if handler is None:
                raise RuntimeError(f"no handler for {job.kind}")
            handler(db, job)
            job.status = JobStatus.SUCCEEDED
            db.commit()
        except Exception as exc:  # noqa: BLE001 - every failure must be recorded, not lost
            db.rollback()
            if isinstance(exc, AIError):
                code, message = exc.code, exc.user_message
            else:
                log.exception("Job %s (%s) failed", job_id, job.kind)
                code, message = "JOB_FAILED", "Amalni bajarishda xatolik yuz berdi. Qayta urinib ko'ring."
            job = db.get(AIJob, job_id)
            job.status = JobStatus.FAILED
            job.error_code = code
            job.error_message = message
            hook = _failure_hooks.get(job.kind)
            if hook:
                try:
                    hook(db, job, code, message)
                except Exception:
                    log.exception("Failure hook for job %s failed", job_id)
            db.commit()


def recover_interrupted_jobs() -> int:
    """On startup, jobs left running by a crashed process are marked failed so they can be retried."""
    with SessionLocal() as db:
        jobs = db.scalars(select(AIJob).where(AIJob.status.in_([JobStatus.QUEUED, JobStatus.RUNNING]))).all()
        for job in jobs:
            job.status = JobStatus.FAILED
            job.error_code = "INTERRUPTED"
            job.error_message = "Server qayta ishga tushgani sababli amal to'xtadi. Qayta urinib ko'ring."
            hook = _failure_hooks.get(job.kind)
            if hook:
                try:
                    hook(db, job, job.error_code, job.error_message)
                except Exception:
                    log.exception("Failure hook during recovery failed")
        db.commit()
        return len(jobs)


def job_view(job: AIJob | None) -> dict | None:
    if job is None:
        return None
    return {"id": str(job.id), "kind": job.kind, "status": job.status.value, "resource_type": job.resource_type,
            "resource_id": str(job.resource_id), "error_code": job.error_code, "error_message": job.error_message,
            "created_at": job.created_at.isoformat(), "updated_at": job.updated_at.isoformat() if job.updated_at else None}
