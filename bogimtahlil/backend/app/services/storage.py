"""Himoyalangan vaqtinchalik fayllar katalogi.

Fayl nomlari faqat server tomonidan (UUID + qat’iy tur nomi) yaratiladi — foydalanuvchi yuborgan
fayl nomi hech qachon yo‘l sifatida ishlatilmaydi.
"""
from __future__ import annotations

import os
import shutil
from pathlib import Path

import numpy as np
from PIL import Image

ARTIFACT_FILES = {
    "original": "original.png",
    "heatmap": "heatmap.png",
    "overlay": "overlay.png",
    "report": "report.pdf",
}


class Storage:
    def __init__(self, root: Path):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        try:
            os.chmod(self.root, 0o700)
        except OSError:
            pass

    def analysis_dir(self, analysis_id: str) -> Path:
        # analysis_id — server yaratgan UUID; qo‘shimcha himoya sifatida tekshiriladi
        if not all(c in "0123456789abcdef-" for c in analysis_id) or len(analysis_id) != 36:
            raise ValueError("Noto‘g‘ri identifikator")
        d = self.root / analysis_id
        d.mkdir(parents=True, exist_ok=True)
        return d

    def relpath(self, analysis_id: str, artifact_type: str) -> str:
        return f"{analysis_id}/{ARTIFACT_FILES[artifact_type]}"

    def abspath(self, rel: str) -> Path:
        p = (self.root / rel).resolve()
        if self.root not in p.parents:
            raise ValueError("Ruxsat etilmagan yo‘l")
        return p

    def save_png(self, analysis_id: str, artifact_type: str, array: np.ndarray) -> str:
        self.analysis_dir(analysis_id)
        rel = self.relpath(analysis_id, artifact_type)
        # Qayta kodlash: EXIF va boshqa metama’lumotlar saqlanmaydi (anonimlashtirish)
        Image.fromarray(array).save(self.abspath(rel), format="PNG", compress_level=3)
        return rel

    def save_bytes(self, analysis_id: str, artifact_type: str, data: bytes) -> str:
        self.analysis_dir(analysis_id)
        rel = self.relpath(analysis_id, artifact_type)
        self.abspath(rel).write_bytes(data)
        return rel

    def delete_analysis(self, analysis_id: str) -> None:
        d = self.root / analysis_id
        if d.is_dir() and d.resolve().parent == self.root:
            shutil.rmtree(d, ignore_errors=True)
