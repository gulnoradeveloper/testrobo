"""OAI (Osteoarthritis Initiative) yorliqlarini tasvirlar bilan bog‘lab, manifest yaratish.

Ikki manba birlashtiriladi:
  1. KL yorliqlari — kXR_SQ_BU## fayllari (har biri bitta tashrif). Ustun nomlari `configs/oai_columns.yaml` da.
  2. Tasvir indeksi — bitta tizza kesmalari: image_path, patient_id, knee_side, visit_id, projection.

Kalit: (patient_id, knee_side, visit_id). Har bir tasvir AYNAN BITTA yorliq bilan bog‘lanishi shart;
bog‘lanmagan, takrorlangan yoki ziddiyatli yozuvlar chiqarilib, hisobotda sanab beriladi.
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from .data import FRONTAL_VIEWS, MANIFEST_COLUMNS

_LEADING_INT = re.compile(r"^\s*(-?\d+)(?:\s*[:.]|\s*$)")
_VISIT_FROM_NAME = re.compile(r"(\d{2})(?=\D*$)")


class OAIFormatError(ValueError):
    pass


def load_config(path: str | Path) -> dict:
    import yaml

    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def parse_code(value) -> int | None:
    """OAI kodli qiymatidan butun sonni ajratadi: "2", "2: 2", "1: Right" → 2/1.
    Yetishmayotgan qiymat kodlari (".", ".A: Not Expected" kabi) va bo‘sh qiymatlar → None."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, (int,)) and not isinstance(value, bool):
        return int(value)
    if isinstance(value, float):
        return int(value) if value.is_integer() else None
    m = _LEADING_INT.match(str(value))
    return int(m.group(1)) if m else None


def _require(df: pd.DataFrame, cols: list[str], source: str) -> None:
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise OAIFormatError(
            f"{source}: kutilgan ustunlar topilmadi {missing}. Mavjud ustunlar: {list(df.columns)[:40]}. "
            "configs/oai_columns.yaml dagi nomlarni OAI data dictionary bilan solishtiring."
        )


def visit_from_filename(path: str | Path, visits: dict) -> str:
    m = _VISIT_FROM_NAME.search(Path(path).stem)
    if not m:
        raise OAIFormatError(f"Fayl nomidan tashrif kodini aniqlab bo‘lmadi: {Path(path).name}")
    visit = f"V{m.group(1)}"
    if visit not in visits:
        raise OAIFormatError(f"{visit} tashrifi konfiguratsiyada yo‘q: {sorted(visits)}")
    return visit


def read_kl_labels(path: str | Path, cfg: dict, visit: str | None = None) -> tuple[pd.DataFrame, dict]:
    """Bitta kXR_SQ_BU fayli → uzun formatdagi jadval (patient_id, knee_side, visit_id, kl_grade, read_project)."""
    lc = cfg["labels"]
    visit = visit or visit_from_filename(path, cfg["visits"])
    raw = pd.read_csv(path, sep=lc.get("delimiter", "|"), dtype=str, keep_default_na=False)
    raw.columns = [c.strip().upper() for c in raw.columns]
    kl_col = lc["kl_column_template"].format(visit=visit).upper()
    pid, side, prj = lc["patient_id"].upper(), lc["knee_side"].upper(), (lc.get("read_project") or "").upper()
    _require(raw, [pid, side, kl_col], Path(path).name)

    side_codes = {int(k): str(v).upper() for k, v in lc["side_codes"].items()}
    out = pd.DataFrame({
        "patient_id": raw[pid].str.strip(),
        "knee_side": raw[side].map(parse_code).map(side_codes),
        "visit_id": visit,
        "kl_grade": raw[kl_col].map(parse_code),
        "read_project": raw[prj].str.strip() if prj and prj in raw.columns else "",
        "label_file": Path(path).name,
    })
    stats = {
        "file": Path(path).name, "visit": visit, "rows": int(len(out)),
        "missing_kl": int(out["kl_grade"].isna().sum()),
        "invalid_kl": int((out["kl_grade"].notna() & ~out["kl_grade"].isin(range(5))).sum()),
        "unknown_side": int(out["knee_side"].isna().sum()),
    }
    out = out[out["kl_grade"].isin(range(5)) & out["knee_side"].isin(["L", "R"]) & (out["patient_id"] != "")]
    out["kl_grade"] = out["kl_grade"].astype(int)
    stats["usable"] = int(len(out))
    return out.reset_index(drop=True), stats


def resolve_duplicate_reads(labels: pd.DataFrame, policy: str = "agree_or_drop",
                            priority: list[str] | None = None) -> tuple[pd.DataFrame, dict]:
    """Bitta tizza/tashrif uchun bir nechta o‘qishni yagona yorliqqa keltirish."""
    key = ["patient_id", "knee_side", "visit_id"]
    grp = labels.groupby(key)["kl_grade"]
    n_reads = grp.transform("size")
    n_unique = grp.transform("nunique")
    stats = {"keys_total": int(labels[key].drop_duplicates().shape[0]),
             "keys_with_multiple_reads": int(labels[n_reads > 1][key].drop_duplicates().shape[0]),
             "keys_with_conflicting_reads": int(labels[n_unique > 1][key].drop_duplicates().shape[0])}
    if policy == "agree_or_drop":
        kept = labels[n_unique == 1].drop_duplicates(subset=key)
    elif policy == "prefer_project":
        if not priority:
            raise OAIFormatError("prefer_project siyosati uchun read_project_priority ro‘yxati bo‘sh")
        rank = {p: i for i, p in enumerate(priority)}
        tmp = labels.assign(_rank=labels["read_project"].map(rank)).dropna(subset=["_rank"])
        kept = tmp.sort_values("_rank").drop_duplicates(subset=key).drop(columns="_rank")
    else:
        raise OAIFormatError(f"Noma’lum duplicate_policy: {policy}")
    stats["keys_kept"] = int(len(kept))
    return kept.reset_index(drop=True), stats


def read_image_index(path: str | Path, cfg: dict) -> pd.DataFrame:
    idx = pd.read_csv(path, sep=cfg.get("image_index", {}).get("delimiter", ","), dtype=str, keep_default_na=False)
    _require(idx, ["image_path", "patient_id", "knee_side", "visit_id", "projection"], Path(path).name)
    idx = idx.copy()
    for c in ("patient_id", "knee_side", "visit_id", "projection"):
        idx[c] = idx[c].str.strip()
    for c in ("knee_side", "visit_id", "projection"):
        idx[c] = idx[c].str.upper()
    base = Path(path).parent
    idx["image_path"] = [str(p if Path(p).is_absolute() else base / p) for p in idx["image_path"]]
    return idx


def link_images_to_labels(images: pd.DataFrame, labels: pd.DataFrame, source: str = "OAI") -> tuple[pd.DataFrame, dict]:
    """Tasvirlarni yorliqlar bilan 1:1 bog‘lash. Noaniq holatlar chiqariladi va sanaladi."""
    key = ["patient_id", "knee_side", "visit_id"]
    stats: dict = {"images_in_index": int(len(images))}
    bad_side = ~images["knee_side"].isin(["L", "R"])
    non_frontal = ~images["projection"].isin(FRONTAL_VIEWS)
    stats["images_bad_side"] = int(bad_side.sum())
    stats["images_non_frontal"] = int(non_frontal.sum())
    imgs = images[~bad_side & ~non_frontal]
    dup_img_key = imgs.duplicated(subset=key, keep=False)
    stats["images_with_duplicate_key"] = int(dup_img_key.sum())  # bitta tizza/tashrif uchun bir nechta tasvir
    imgs = imgs[~dup_img_key]
    if labels.duplicated(subset=key).any():
        raise OAIFormatError("Yorliqlarda takrorlangan kalitlar qolgan — avval resolve_duplicate_reads bajaring")
    merged = imgs.merge(labels[key + ["kl_grade", "read_project", "label_file"]], on=key, how="left",
                        validate="one_to_one", indicator=True)
    stats["images_without_label"] = int((merged["_merge"] == "left_only").sum())
    linked = merged[merged["_merge"] == "both"].drop(columns="_merge").copy()
    linked["kl_grade"] = linked["kl_grade"].astype(int)
    linked["dataset_source"] = source
    stats["linked"] = int(len(linked))
    stats["labels_without_image"] = int(len(labels) - len(linked))
    cols = [c for c in MANIFEST_COLUMNS if c != "split"] + ["read_project", "label_file"]
    return linked[cols].reset_index(drop=True), stats
