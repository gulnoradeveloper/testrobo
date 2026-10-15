"""Dataset manifest, bemor bo‘yicha ajratish va PyTorch Dataset.

Manifest CSV ustunlari (TT: modelni o‘qitish bosqichi, 2-band):
    image_path      — bitta tizza tasviri fayliga yo‘l (manifestga nisbatan yoki absolyut)
    patient_id      — bemorning anonim identifikatori (OAI: ID)
    knee_side       — "L" yoki "R" (qaysi tizza)
    visit_id        — tashrif kodi (OAI: V00, V01, V03, ...)
    projection      — rentgen proyeksiyasi, masalan "PA" (frontal)
    kl_grade        — 0..4
    dataset_source  — ma’lumot manbasi, masalan "OAI"
    split           — "train" | "val" | "test" (prepare_dataset.py qo‘shadi)

Eski nomlar (side, timepoint, view) avtomatik yangi nomlarga o‘tkaziladi.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd

from . import KL_CLASSES
from .preprocess import DEFAULT_CONFIG, PreprocessConfig, decode_grayscale, letterbox, normalize_to_chw

REQUIRED_COLUMNS = ("image_path", "patient_id", "knee_side", "visit_id", "projection", "kl_grade")
MANIFEST_COLUMNS = (*REQUIRED_COLUMNS, "dataset_source", "split")
LEGACY_COLUMNS = {"side": "knee_side", "timepoint": "visit_id", "view": "projection"}
FRONTAL_VIEWS = {"PA", "AP", "FRONTAL", "PA_FIXED_FLEXION"}
SPLITS = ("train", "val", "test")


class ManifestError(ValueError):
    pass


def load_manifest(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    df = pd.read_csv(path, dtype=str, keep_default_na=False, na_values=[""])
    df = df.rename(columns={k: v for k, v in LEGACY_COLUMNS.items() if k in df.columns and v not in df.columns})
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ManifestError(f"Manifestda ustunlar yo‘q: {missing}")
    df["kl_grade"] = pd.to_numeric(df["kl_grade"], errors="coerce")
    for c in ("knee_side", "projection"):
        df[c] = df[c].astype(str).str.strip().str.upper()
    if "dataset_source" not in df.columns:
        df["dataset_source"] = "noma’lum"
    base = path.parent
    df["image_path"] = [str(p if Path(p).is_absolute() else (base / p)) for p in df["image_path"]]
    return df


def validate_manifest(df: pd.DataFrame, check_files: bool = True) -> dict:
    """Yorliqlar, proyeksiya, takrorlar va fayllar mavjudligini tekshiradi. Hisobot qaytaradi."""
    issues: list[str] = []
    bad_grade = ~df["kl_grade"].isin(list(range(len(KL_CLASSES))))
    if bad_grade.any():
        issues.append(f"{int(bad_grade.sum())} ta yozuvda KL bahosi 0..4 oralig‘ida emas")
    bad_side = ~df["knee_side"].isin(["L", "R"])
    if bad_side.any():
        issues.append(f"{int(bad_side.sum())} ta yozuvda tizza tomoni (L/R) noaniq")
    non_frontal = ~df["projection"].isin(FRONTAL_VIEWS)
    if non_frontal.any():
        issues.append(f"{int(non_frontal.sum())} ta yozuv frontal proyeksiya emas — o‘qitishdan chiqariladi")
    key_dup = df.duplicated(subset=["patient_id", "knee_side", "visit_id"], keep=False)
    if key_dup.any():
        issues.append(f"{int(key_dup.sum())} ta yozuvda (bemor, tomon, vaqt nuqtasi) kaliti takrorlangan")
    missing_files = 0
    if check_files:
        missing_files = int(sum(not Path(p).is_file() for p in df["image_path"]))
        if missing_files:
            issues.append(f"{missing_files} ta tasvir fayli topilmadi")
    return {
        "n_records": int(len(df)),
        "n_patients": int(df["patient_id"].nunique()),
        "invalid_grades": int(bad_grade.sum()),
        "invalid_sides": int(bad_side.sum()),
        "non_frontal": int(non_frontal.sum()),
        "duplicate_keys": int(key_dup.sum()),
        "missing_files": missing_files,
        "issues": issues,
    }


def file_sha256(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def find_duplicate_images(df: pd.DataFrame) -> pd.DataFrame:
    """Bayt darajasida bir xil tasvirlarni aniqlaydi (sha256)."""
    df = df.copy()
    df["image_sha256"] = [file_sha256(p) for p in df["image_path"]]
    return df


def patient_split(df: pd.DataFrame, val_frac: float = 0.15, test_frac: float = 0.15, seed: int = 42) -> pd.DataFrame:
    """Bemorlar bo‘yicha stratifikatsiyalangan ajratish — bitta bemor faqat bitta guruhda bo‘ladi.

    Har bir bemor uchun eng yuqori KL bahosi stratifikatsiya belgisi sifatida olinadi.
    """
    rng = np.random.default_rng(seed)
    patient_grade = df.groupby("patient_id")["kl_grade"].max()
    assignment: dict[str, str] = {}
    for _grade, patients in patient_grade.groupby(patient_grade):
        ids = patients.index.to_numpy().copy()
        rng.shuffle(ids)
        n = len(ids)
        n_test = int(round(n * test_frac))
        n_val = int(round(n * val_frac))
        for pid in ids[:n_test]:
            assignment[pid] = "test"
        for pid in ids[n_test:n_test + n_val]:
            assignment[pid] = "val"
        for pid in ids[n_test + n_val:]:
            assignment[pid] = "train"
    out = df.copy()
    out["split"] = out["patient_id"].map(assignment)
    return out


def split_summary(df: pd.DataFrame) -> dict:
    """Har bir guruh: tasvirlar, bemorlar, KL0–KL4 sinflar soni va ulushi."""
    out = {}
    n_pat = df["patient_id"].nunique()
    for split in SPLITS:
        part = df[df["split"] == split]
        vc = part["kl_grade"].astype(int).value_counts().reindex(range(len(KL_CLASSES)), fill_value=0)
        out[split] = {
            "images": int(len(part)),
            "patients": int(part["patient_id"].nunique()),
            "patient_fraction": float(part["patient_id"].nunique() / n_pat) if n_pat else 0.0,
            "classes": {KL_CLASSES[i]: int(vc[i]) for i in range(len(KL_CLASSES))},
        }
    return out


def check_patient_leakage(df: pd.DataFrame) -> list[str]:
    """Bir nechta guruhga tushib qolgan bemorlar ro‘yxati (bo‘sh bo‘lishi shart)."""
    counts = df.groupby("patient_id")["split"].nunique()
    return counts[counts > 1].index.tolist()


def class_distribution(df: pd.DataFrame) -> dict:
    out = {}
    for split, part in df.groupby("split"):
        vc = part["kl_grade"].value_counts().reindex(range(len(KL_CLASSES)), fill_value=0)
        out[str(split)] = {KL_CLASSES[i]: int(vc[i]) for i in range(len(KL_CLASSES))}
    return out


def class_weights(labels, num_classes: int = len(KL_CLASSES)) -> np.ndarray:
    """Weighted Cross-Entropy uchun teskari chastota vaznlari (o‘rtacha = 1)."""
    counts = np.bincount(np.asarray(labels, dtype=int), minlength=num_classes).astype(np.float64)
    counts[counts == 0] = 1.0
    w = counts.sum() / (num_classes * counts)
    return (w / w.mean()).astype(np.float32)


class KneeXrayDataset:
    """torch.utils.data.Dataset bilan mos (import torch faqat ishlatilganda)."""

    def __init__(self, df: pd.DataFrame, cfg: PreprocessConfig = DEFAULT_CONFIG, augment: bool = False, seed: int = 42):
        self.paths = df["image_path"].tolist()
        self.labels = df["kl_grade"].astype(int).tolist()
        self.cfg = cfg
        self.augment = augment
        self.rng = np.random.default_rng(seed)

    def __len__(self) -> int:
        return len(self.paths)

    def _augment(self, img: np.ndarray) -> np.ndarray:
        from PIL import Image

        pil = Image.fromarray(img)
        if self.rng.random() < 0.5:
            pil = pil.transpose(Image.FLIP_LEFT_RIGHT)
        angle = float(self.rng.uniform(-7, 7))
        pil = pil.rotate(angle, resample=Image.BILINEAR, fillcolor=self.cfg.pad_value)
        arr = np.asarray(pil, dtype=np.float32)
        contrast = float(self.rng.uniform(0.85, 1.15))
        brightness = float(self.rng.uniform(-15, 15))
        arr = (arr - arr.mean()) * contrast + arr.mean() + brightness
        return np.clip(arr, 0, 255).astype(np.uint8)

    def __getitem__(self, idx: int):
        import torch

        gray = decode_grayscale(self.paths[idx])
        boxed, _ = letterbox(gray, self.cfg)
        if self.augment:
            boxed = self._augment(boxed)
        x = normalize_to_chw(boxed, self.cfg)
        return torch.from_numpy(x), self.labels[idx]
