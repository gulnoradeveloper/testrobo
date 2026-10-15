"""Tasvirga dastlabki ishlov berish — training va inference uchun yagona konfiguratsiya.

Asosiy tamoyil: tasvir hech qachon kesilmaydi. Avval kvadratga to‘ldiriladi (letterbox),
so‘ng 224×224 ga kichraytiriladi — shu tufayli bo‘g‘im yorig‘i, osteofitlar kabi
chekkadagi anatomik belgilar yo‘qolmaydi. Grad-CAM xaritasi keyin aynan shu
geometriya bo‘yicha asl tasvir koordinatalariga qaytariladi.
"""
from __future__ import annotations

import io
from dataclasses import asdict, dataclass, field
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps

PREPROCESS_VERSION = "pp-v1"


@dataclass(frozen=True)
class PreprocessConfig:
    version: str = PREPROCESS_VERSION
    input_size: int = 224
    # Grayscale rentgen 3 kanalga takrorlanadi va ImageNet statistikasi bilan normallashtiriladi
    mean: tuple[float, float, float] = (0.485, 0.456, 0.406)
    std: tuple[float, float, float] = (0.229, 0.224, 0.225)
    pad_value: int = 0
    resample: str = "bilinear"

    def to_dict(self) -> dict:
        d = asdict(self)
        d["mean"] = list(self.mean)
        d["std"] = list(self.std)
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "PreprocessConfig":
        return cls(
            version=str(d["version"]),
            input_size=int(d["input_size"]),
            mean=tuple(float(x) for x in d["mean"]),
            std=tuple(float(x) for x in d["std"]),
            pad_value=int(d.get("pad_value", 0)),
            resample=str(d.get("resample", "bilinear")),
        )


DEFAULT_CONFIG = PreprocessConfig()


@dataclass(frozen=True)
class LetterboxMeta:
    """Asl tasvirdan model kirishiga o‘tish geometriyasi (heatmapni qaytarish uchun)."""

    orig_width: int
    orig_height: int
    side: int  # kvadrat tomoni (asl piksellarda)
    pad_left: int
    pad_top: int
    input_size: int = field(default=224)


def decode_grayscale(data: bytes | str | Path) -> np.ndarray:
    """Faylni dekodlab, EXIF orientatsiyasini qo‘llab, 8-bit grayscale massivga aylantiradi."""
    if isinstance(data, (str, Path)):
        img = Image.open(data)
    else:
        img = Image.open(io.BytesIO(data))
    img.load()
    img = ImageOps.exif_transpose(img)
    return to_grayscale_array(img)


def to_grayscale_array(img: Image.Image) -> np.ndarray:
    if img.mode in ("I;16", "I;16B", "I;16L", "I"):
        arr = np.asarray(img, dtype=np.float32)
        lo, hi = float(arr.min()), float(arr.max())
        arr = (arr - lo) / (hi - lo) * 255.0 if hi > lo else np.zeros_like(arr)
        return arr.astype(np.uint8)
    if img.mode in ("RGBA", "LA", "P"):
        img = img.convert("RGBA")
        bg = Image.new("RGBA", img.size, (0, 0, 0, 255))
        img = Image.alpha_composite(bg, img)
    return np.asarray(img.convert("L"), dtype=np.uint8)


def letterbox(gray: np.ndarray, cfg: PreprocessConfig = DEFAULT_CONFIG) -> tuple[np.ndarray, LetterboxMeta]:
    """Kesmasdan kvadratga to‘ldirish va input_size ga o‘lchamlash."""
    if gray.ndim != 2:
        raise ValueError("Grayscale (H×W) massiv kutilgan")
    h, w = gray.shape
    side = max(h, w)
    pad_top = (side - h) // 2
    pad_left = (side - w) // 2
    canvas = np.full((side, side), cfg.pad_value, dtype=np.uint8)
    canvas[pad_top:pad_top + h, pad_left:pad_left + w] = gray
    resample = Image.BILINEAR if cfg.resample == "bilinear" else Image.BICUBIC
    resized = Image.fromarray(canvas).resize((cfg.input_size, cfg.input_size), resample)
    meta = LetterboxMeta(w, h, side, pad_left, pad_top, cfg.input_size)
    return np.asarray(resized, dtype=np.uint8), meta


def normalize_to_chw(img: np.ndarray, cfg: PreprocessConfig = DEFAULT_CONFIG) -> np.ndarray:
    """uint8 H×W → float32 3×H×W, normallashtirilgan."""
    x = img.astype(np.float32) / 255.0
    x = np.repeat(x[None, :, :], 3, axis=0)
    mean = np.asarray(cfg.mean, dtype=np.float32)[:, None, None]
    std = np.asarray(cfg.std, dtype=np.float32)[:, None, None]
    return (x - mean) / std


def preprocess_array(gray: np.ndarray, cfg: PreprocessConfig = DEFAULT_CONFIG) -> tuple[np.ndarray, LetterboxMeta]:
    boxed, meta = letterbox(gray, cfg)
    return normalize_to_chw(boxed, cfg), meta


def heatmap_to_original(cam: np.ndarray, meta: LetterboxMeta) -> np.ndarray:
    """Model kirishidagi (input_size×input_size) xaritani asl tasvir o‘lchamiga qaytaradi."""
    cam_img = Image.fromarray(cam.astype(np.float32))
    full = np.asarray(cam_img.resize((meta.side, meta.side), Image.BILINEAR), dtype=np.float32)
    out = full[meta.pad_top:meta.pad_top + meta.orig_height, meta.pad_left:meta.pad_left + meta.orig_width]
    return np.clip(out, 0.0, 1.0)
