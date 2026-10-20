import logging
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import APIRouter, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.api.deps import limiter
from app.api.v1 import admin, auth, defenses, me, practice, projects
from app.core.config import get_settings
from app.core.database import SessionLocal
from app.core.errors import AppError, install_error_handlers
from app.services import jobs
from app.services.defense.workflow import register_handlers as register_defense
from app.services.projects.analysis import register_handlers as register_analysis

settings = get_settings()
logging.basicConfig(level=settings.LOG_LEVEL, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("communiai")

register_analysis()
register_defense()


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.APP_ENV == "production" and settings.JWT_SECRET.startswith("change-me"):
        raise RuntimeError("JWT_SECRET must be set in production")
    try:
        n = jobs.recover_interrupted_jobs()
        if n:
            log.warning("Marked %d interrupted AI jobs as failed (retryable)", n)
    except Exception:
        log.exception("Job recovery failed (database not ready?)")
    log.info("CommuniAI API started (env=%s, ai_configured=%s, model=%s)",
             settings.APP_ENV, settings.ai_configured, settings.AI_MODEL)
    yield


app = FastAPI(
    title="CommuniAI API",
    version="1.0.0",
    description="AI asosida IT loyihalarini himoya qilish va kasbiy kommunikativ kompetentlikni rivojlantirish platformasi.",
    lifespan=lifespan,
)
install_error_handlers(app)

if settings.cors_origins:
    app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_credentials=False,
                       allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE"],
                       allow_headers=["Authorization", "Content-Type", "Idempotency-Key"])


@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
    request.state.request_id = request_id[:64]
    started = time.monotonic()
    if request.url.path.startswith("/api/"):
        ip = request.client.host if request.client else "unknown"
        try:
            limiter.check(f"global:{ip}", settings.RATE_LIMIT_PER_MINUTE)
        except AppError as e:
            return JSONResponse(status_code=429, content={"error": {"code": e.code, "message": e.message,
                                                                    "details": e.details}})
    response = await call_next(request)
    elapsed = int((time.monotonic() - started) * 1000)
    response.headers["X-Request-ID"] = request.state.request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Cache-Control"] = "no-store"
    # Never log query strings or bodies (may contain tokens / personal data).
    log.info("%s %s -> %s (%d ms) rid=%s", request.method, request.url.path, response.status_code, elapsed,
             request.state.request_id)
    return response


api = APIRouter(prefix="/api/v1")
for r in (auth.router, projects.router, defenses.router, practice.router, me.router, admin.router):
    api.include_router(r)
app.include_router(api)


# Optional: the Flutter web build of the app served at /app/ (same origin as the API).
_WEB_DIR = Path(__file__).resolve().parent.parent / "web_app"
if (_WEB_DIR / "index.html").exists():
    app.mount("/app", StaticFiles(directory=_WEB_DIR, html=True), name="web_app")

    @app.get("/", include_in_schema=False)
    def _root():
        return RedirectResponse("/app/")


@app.get("/health/live", tags=["System"])
def live():
    return {"status": "ok"}


@app.get("/health/ready", tags=["System"])
def ready():
    checks = {"database": "ok", "ai_provider": "configured" if settings.ai_configured else "not_configured",
              "email": "configured" if settings.email_enabled else "not_configured"}
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
    except Exception:
        checks["database"] = "error"
        return JSONResponse(status_code=503, content={"status": "not_ready", "checks": checks})
    return {"status": "ready", "checks": checks}


@app.get("/api/v1/meta", tags=["System"])
def meta():
    """Public, non-secret capability flags for the mobile client."""
    return {"version": app.version, "ai_configured": settings.ai_configured, "email_enabled": settings.email_enabled,
            "max_upload_mb": settings.MAX_UPLOAD_SIZE_MB, "rubric_version": settings.RUBRIC_VERSION,
            "allowed_extensions": ["pdf", "docx", "pptx", "txt"]}
