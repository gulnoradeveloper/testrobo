"""Yuklangan faylni server tomonida tekshirish.

Tekshiruvlar: bo‘sh fayl, hajm, kengaytma, e’lon qilingan MIME, faylning haqiqiy imzosi (magic bytes),
Pillow orqali to‘liq dekodlash, piksel soni (decompression bomb), minimal o‘lcham va tasvirning
texnik o‘qilishi (bir xil rangli bo‘sh tasvir emasligi).

DIQQAT: bu tekshiruvlar rentgen proyeksiyasini yoki anatomik sohani ANIQLAMAYDI — buni
foydalanuvchi tasdiqlaydi (projection_confirmed).
"""
from __future__ import annotations

import io
import warnings
from dataclasses import dataclass

import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError

from kltool.preprocess import to_grayscale_array

from ..errors import ApiError

ALLOWED_EXTENSIONS = {".jpg": "jpeg", ".jpeg": "jpeg", ".png": "png"}
ALLOWED_MIME = {"image/jpeg": "jpeg", "image/jpg": "jpeg", "image/pjpeg": "jpeg", "image/png": "png"}


@dataclass
class ValidatedImage:
    gray: np.ndarray  # H×W uint8
    width: int
    height: int
    fmt: str


def sniff_format(data: bytes) -> str | None:
    if data[:3] == b"\xff\xd8\xff":
        return "jpeg"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    return None


def validate_upload(
    data: bytes,
    filename: str | None,
    content_type: str | None,
    max_bytes: int,
    max_pixels: int,
    min_side: int,
) -> ValidatedImage:
    if not data:
        raise ApiError("NO_FILE", 400)
    if len(data) > max_bytes:
        raise ApiError("FILE_TOO_LARGE", 413)

    real = sniff_format(data)
    if real is None:
        raise ApiError("UNSUPPORTED_FORMAT", 415)

    ext = ("." + filename.rsplit(".", 1)[-1].lower()) if filename and "." in filename else ""
    if ext and ext not in ALLOWED_EXTENSIONS:
        raise ApiError("UNSUPPORTED_FORMAT", 415)
    if ext and ALLOWED_EXTENSIONS[ext] != real:
        raise ApiError("UNSUPPORTED_FORMAT", 415, details={"reason": "kengaytma fayl tarkibiga mos emas"})
    declared = (content_type or "").split(";")[0].strip().lower()
    if declared and declared != "application/octet-stream":
        if declared not in ALLOWED_MIME or ALLOWED_MIME[declared] != real:
            raise ApiError("UNSUPPORTED_FORMAT", 415, details={"reason": "MIME turi fayl tarkibiga mos emas"})

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            probe = Image.open(io.BytesIO(data))
            w, h = probe.size
            if w * h > max_pixels:
                raise ApiError("IMAGE_DIMENSIONS", 422, details={"max_pixels": max_pixels})
            probe.verify()  # strukturaviy yaxlitlik
            img = Image.open(io.BytesIO(data))
            img.load()  # to‘liq dekodlash (kesilgan fayllar shu yerda aniqlanadi)
    except ApiError:
        raise
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError, Image.DecompressionBombWarning,
            Image.DecompressionBombError):
        raise ApiError("IMAGE_UNREADABLE", 422) from None

    if (img.format or "").lower() != real:
        raise ApiError("UNSUPPORTED_FORMAT", 415)

    img = ImageOps.exif_transpose(img)
    w, h = img.size
    if min(w, h) < min_side:
        raise ApiError("IMAGE_DIMENSIONS", 422, details={"min_side": min_side})

    gray = to_grayscale_array(img)
    if float(gray.std()) < 2.0:
        raise ApiError("IMAGE_UNREADABLE", 422, details={"reason": "tasvir deyarli bir xil rangda — tasvir ma’lumoti yo‘q"})
    return ValidatedImage(gray=gray, width=w, height=h, fmt=real)
