"""Model sahifasi uchun tajriba ma’lumotlari — FAQAT mavjud fayllardan o‘qiladi.

Manbalar (ai/scripts natijalari):
  data/splits/dataset_report.json           — dataset hajmi, bemorlar, KL0–KL4 taqsimoti
  experiments/<arch>/history.csv            — har bir epoch: train/val loss, accuracy, macro F1
  experiments/<arch>/train_summary.json     — eng yaxshi epoch, davomiylik
  experiments/<arch>/eval_val.json          — validation metrikalari
  experiments/model_comparison.json         — validation bo‘yicha tanlov
  experiments/<tanlangan>/eval_test.json    — mustaqil test (yoki model.pt ichidagi metrics.test)
Fayl bo‘lmasa, tegishli bo‘lim {"available": false} qaytaradi — hech qanday qiymat to‘ldirilmaydi.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from kltool import KL_CLASSES

ARCHS = {"resnet18": "ResNet-18", "efficientnet_b0": "EfficientNet-B0"}
METRIC_KEYS = ("accuracy", "balanced_accuracy", "macro_precision", "macro_recall", "macro_f1", "quadratic_weighted_kappa")
HISTORY_COLS = ("epoch", "train_loss", "val_loss", "train_accuracy", "val_accuracy", "val_macro_f1", "val_qwk")
MAX_EPOCHS = 500


def _json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None
    except (OSError, ValueError):
        return None


def _metrics(m: dict | None) -> dict | None:
    if not m or "accuracy" not in m:
        return None
    return {
        **{k: m.get(k) for k in METRIC_KEYS},
        "n_samples": m.get("n_samples"),
        "n_patients": m.get("n_patients"),
        "recall": {c: m["per_class"][c]["recall"] for c in KL_CLASSES if c in m.get("per_class", {})},
        "confusion_matrix": m.get("confusion_matrix"),
        "early_grade_error_rate": (m.get("early_grade_confusion") or {}).get("error_rate_within_kl0_kl2"),
    }


def _history(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    rows = []
    with open(path, encoding="utf-8", newline="") as f:
        for i, row in enumerate(csv.DictReader(f)):
            if i >= MAX_EPOCHS:
                break
            out: dict[str, Any] = {}
            for k in HISTORY_COLS:
                try:
                    out[k] = int(row[k]) if k == "epoch" else round(float(row[k]), 5)
                except (KeyError, TypeError, ValueError):
                    out[k] = None
            rows.append(out)
    return rows


def collect(experiments_dir: Path, splits_dir: Path, model_metrics: dict | None, model_dataset: dict | None) -> dict:
    exp = Path(experiments_dir)

    ds = _json(Path(splits_dir) / "dataset_report.json")
    dataset: dict[str, Any] = {"available": bool(ds), "name": (model_dataset or {}).get("name")}
    if ds:
        dataset.update(
            images=ds.get("totals", {}).get("images"), patients=ds.get("totals", {}).get("patients"),
            sources=ds.get("totals", {}).get("sources"), split_rule=ds.get("split_source"),
            patients_in_multiple_splits=ds.get("patient_leakage", {}).get("n_patients_in_multiple_splits"),
            patient_ids_verified=ds.get("patient_ids_verified", True),
            patient_ids_note=ds.get("patient_ids_note"),
            splits={s: {"images": v.get("images"), "patients": v.get("patients"), "classes": v.get("classes")}
                    for s, v in (ds.get("splits") or {}).items()},
        )

    training = {}
    for arch, title in ARCHS.items():
        d = exp / arch
        summ = _json(d / "train_summary.json")
        hist = _history(d / "history.csv")
        val = _metrics(_json(d / "eval_val.json") or _json(d / "val_metrics.json"))
        training[arch] = {
            "title": title, "available": bool(hist or summ or val), "history": hist, "validation": val,
            "best_epoch": (summ or {}).get("best_epoch"), "epochs_run": (summ or {}).get("epochs_run"),
            "training_minutes": round(summ["training_seconds"] / 60, 1) if summ and summ.get("training_seconds") else None,
            "pretrained": (summ or {}).get("pretrained"),
        }

    cmp = _json(exp / "model_comparison.json")
    comparison = {"available": bool(cmp)}
    selected_dir = None
    if cmp:
        sel = Path(str(cmp.get("selected", ""))).name
        selected_dir = exp / sel if sel in ARCHS else None
        comparison.update(selected=sel if sel in ARCHS else None, selected_title=ARCHS.get(sel),
                          rule=cmp.get("selection_rule"), reason=cmp.get("selected_reason"))

    test_raw = (model_metrics or {}).get("test") or (_json(selected_dir / "eval_test.json") if selected_dir else None)
    return {"dataset": dataset, "training": training, "comparison": comparison,
            "test": {"available": bool(_metrics(test_raw)), **(_metrics(test_raw) or {})},
            "class_names": list(KL_CLASSES)}
