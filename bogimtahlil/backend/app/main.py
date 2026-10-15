"""FastAPI ilovasi: `uvicorn app.main:app`"""
from __future__ import annotations

import asyncio
import contextlib
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from . import __version__
from .api.routes import router
from .config import Settings, get_settings
from .database import make_engine, make_session_factory, run_migrations
from .errors import install_error_handlers
from .ratelimit import RateLimitMiddleware
from .services.analysis import purge_expired, register_model_version
from .services.inference import ModelService
from .services.storage import Storage

# Loglarda faqat texnik ma’lumot: tasvir, fayl nomi yoki cookie yozilmaydi
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("bogimtahlil")


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        run_migrations(settings.database_url)
        app.state.engine = make_engine(settings.database_url)
        app.state.session_factory = make_session_factory(app.state.engine)
        app.state.storage = Storage(settings.storage_dir)
        ms = ModelService(settings)
        ms.load()  # model faqat bir marta, ishga tushishda yuklanadi
        app.state.model_service = ms
        with app.state.session_factory() as db:
            register_model_version(db, ms, settings)
            purge_expired(db, app.state.storage)

        async def cleaner():
            while True:
                await asyncio.sleep(settings.cleanup_interval_minutes * 60)
                try:
                    with app.state.session_factory() as db:
                        n = await asyncio.to_thread(purge_expired, db, app.state.storage)
                    if n:
                        log.info("Muddati o‘tgan %d ta tahlil o‘chirildi", n)
                except Exception:
                    log.exception("Tozalash xatosi")

        task = asyncio.create_task(cleaner())
        yield
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task
        app.state.engine.dispose()

    app = FastAPI(title="Bo‘g‘imTahlil API", version=__version__, lifespan=lifespan,
                  docs_url="/api/docs", openapi_url="/api/openapi.json", redoc_url=None)
    app.state.settings = settings
    install_error_handlers(app)

    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        if settings.force_https:
            proto = request.headers.get("x-forwarded-proto", request.url.scheme) if settings.trust_proxy_headers \
                else request.url.scheme
            if proto != "https":
                return RedirectResponse(str(request.url.replace(scheme="https")), status_code=308)
        resp = await call_next(request)
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("X-Frame-Options", "DENY")
        resp.headers.setdefault("Referrer-Policy", "no-referrer")
        if settings.force_https:
            resp.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        return resp

    app.add_middleware(RateLimitMiddleware, settings=settings)
    app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_credentials=True,
                       allow_methods=["GET", "POST", "DELETE"], allow_headers=["*"])
    app.include_router(router)
    return app


app = create_app()
