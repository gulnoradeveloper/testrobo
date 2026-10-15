"""Yagona xatolik formati:  {"error": {"code": "...", "message": "...", "details": ...}}"""
from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from .messages import ERRORS

log = logging.getLogger("bogimtahlil")


class ApiError(Exception):
    def __init__(self, code: str, status_code: int, message: str | None = None, details: Any = None):
        self.code = code
        self.status_code = status_code
        self.message = message or ERRORS.get(code, ERRORS["INTERNAL_ERROR"])
        self.details = details


def error_body(code: str, message: str, details: Any = None) -> dict:
    body: dict[str, Any] = {"code": code, "message": message}
    if details is not None:
        body["details"] = details
    return {"error": body}


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def _api_error(_req: Request, exc: ApiError):
        return JSONResponse(error_body(exc.code, exc.message, exc.details), status_code=exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def _validation(_req: Request, exc: RequestValidationError):
        fields = [".".join(str(p) for p in e.get("loc", [])) for e in exc.errors()]
        return JSONResponse(error_body("VALIDATION_ERROR", ERRORS["VALIDATION_ERROR"], {"fields": fields}), status_code=422)

    @app.exception_handler(StarletteHTTPException)
    async def _http(_req: Request, exc: StarletteHTTPException):
        if exc.status_code == 404:
            return JSONResponse(error_body("ROUTE_NOT_FOUND", ERRORS["ROUTE_NOT_FOUND"]), status_code=404)
        if exc.status_code == 405:
            return JSONResponse(error_body("METHOD_NOT_ALLOWED", "Ushbu manzil uchun so‘rov usuli ruxsat etilmagan."), status_code=405)
        return JSONResponse(error_body("HTTP_ERROR", ERRORS["INTERNAL_ERROR"]), status_code=exc.status_code)

    @app.exception_handler(Exception)
    async def _unhandled(_req: Request, exc: Exception):
        # Ichki tafsilotlar (yo‘llar, stack) foydalanuvchiga qaytarilmaydi
        log.exception("Kutilmagan xatolik: %s", type(exc).__name__)
        return JSONResponse(error_body("INTERNAL_ERROR", ERRORS["INTERNAL_ERROR"]), status_code=500)
