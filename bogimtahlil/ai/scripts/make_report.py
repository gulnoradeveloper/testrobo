"""Tajriba hisobotini (experiments/EXPERIMENT_REPORT.md) faqat mavjud fayllar asosida yaratish.

    python ai/scripts/make_report.py

Fayl topilmasa, tegishli bo‘limda "MAVJUD EMAS" va uni yaratadigan buyruq yoziladi — hech qanday raqam
taxmin qilinmaydi yoki to‘ldirilmaydi.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from _common import resolve

from kltool import KL_CLASSES
from kltool.checkpoint import CheckpointError, load_checkpoint

NA = "**MAVJUD EMAS**"
KEYS = [("accuracy", "Accuracy"), ("balanced_accuracy", "Balanced Accuracy"), ("macro_precision", "Macro Precision"),
        ("macro_recall", "Macro Recall"), ("macro_f1", "Macro F1"), ("quadratic_weighted_kappa", "Quadratic Weighted Kappa")]


def read(p: Path):
    return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else None


def metrics_block(m: dict | None, how: str) -> list[str]:
    if not m:
        return [f"{NA} — {how}", ""]
    out = [f"Tasvirlar: {m['n_samples']}" + (f", bemorlar: {m['n_patients']}" if m.get("n_patients") else ""), "",
           "| Ko‘rsatkich | Qiymat |", "|---|---|"]
    out += [f"| {name} | {m[k]:.4f} |" for k, name in KEYS]
    out += ["", "| Sinf | Precision | Recall | F1 | Soni |", "|---|---|---|---|---|"]
    out += [f"| {c} | {m['per_class'][c]['precision']:.3f} | {m['per_class'][c]['recall']:.3f} | "
            f"{m['per_class'][c]['f1']:.3f} | {m['per_class'][c]['support']} |" for c in KL_CLASSES]
    out += ["", "Confusion matrix (qator — haqiqiy, ustun — bashorat):", "", "| | " + " | ".join(KL_CLASSES) + " |",
            "|---|" + "---|" * len(KL_CLASSES)]
    out += [f"| **{KL_CLASSES[i]}** | " + " | ".join(str(v) for v in row) + " |" for i, row in enumerate(m["confusion_matrix"])]
    eg = m.get("early_grade_confusion")
    if eg:
        pairs = ", ".join(f"{k}: {v['count']} ({v['rate_of_true_class']:.1%})" for k, v in eg["pairs"].items())
        out += ["", f"KL0–KL2 o‘zaro xatolar: {eg['errors_within_kl0_kl2']} / {eg['samples_kl0_kl2']} "
                    f"({eg['error_rate_within_kl0_kl2']:.1%}). Juftliklar: {pairs}"]
    return out + [""]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--splits-dir", default="data/splits")
    ap.add_argument("--experiments-dir", default="experiments")
    ap.add_argument("--artifacts-dir", default="artifacts")
    ap.add_argument("--out", help="standart: <experiments-dir>/EXPERIMENT_REPORT.md")
    args = ap.parse_args()
    splits, exp, art = resolve(args.splits_dir), resolve(args.experiments_dir), resolve(args.artifacts_dir)

    L = ["# Bo‘g‘imTahlil — model tajribasi hisoboti", "",
         f"Yaratilgan: {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC · manba: `ai/scripts/make_report.py` "
         "(raqamlar faqat tajriba fayllaridan olinadi)", ""]

    ds = read(splits / "dataset_report.json")
    L += ["## 1–2. Ma’lumotlar to‘plami va taqsimot", ""]
    if ds:
        t = ds["totals"]
        verified = ds.get("patient_ids_verified", True)
        if verified:
            L += [f"Jami tasvirlar: **{t['images']}**, bemorlar: **{t['patients']}**, manba: {t['sources']}",
                  f"Ajratish: {ds['split_source']}. Guruhlar orasida kesishgan bemorlar: "
                  f"**{ds['patient_leakage']['n_patients_in_multiple_splits']}**", "",
                  "| Guruh | Tasvirlar | Bemorlar | Bemor ulushi | " + " | ".join(KL_CLASSES) + " |",
                  "|---|---|---|---|" + "---|" * len(KL_CLASSES)]
        else:
            L += [f"Jami tasvirlar: **{t['images']}**, bemorlar: **ma’lum emas** (datasetda bemor ID yo‘q), "
                  f"manba: {', '.join(t['sources'])}",
                  f"Ajratish: {ds['split_source']} (datasetning o‘z train/val/test taqsimoti).", "",
                  "| Guruh | Tasvirlar | Ulushi | " + " | ".join(KL_CLASSES) + " |",
                  "|---|---|---|" + "---|" * len(KL_CLASSES)]
        total = sum(v["images"] for v in ds["splits"].values()) or 1
        for s, v in ds["splits"].items():
            mid = f"{v['patients']} | {v['patient_fraction']:.1%}" if verified else f"{v['images'] / total:.1%}"
            L.append(f"| {s} | {v['images']} | {mid} | " + " | ".join(str(v["classes"][c]) for c in KL_CLASSES) + " |")
        if ds.get("patient_ids_verified") is False:
            L += ["", f"**Cheklov:** {ds['patient_ids_note']}"]
        L += ["", f"Tozalash: {json.dumps(ds['duplicates'], ensure_ascii=False)}", ""]
    else:
        L += [f"{NA} — dataset hali tayyorlanmagan (`build_oai_manifest.py`, so‘ng `prepare_dataset.py`).", ""]

    for arch, title in (("resnet18", "3. ResNet-18"), ("efficientnet_b0", "4. EfficientNet-B0")):
        d = exp / arch
        summ = read(d / "train_summary.json")
        L += [f"## {title} (validation)", ""]
        if summ:
            L += [f"Eng yaxshi epoch: {summ['best_epoch']} / {summ.get('epochs_run')}, o‘qitish vaqti: "
                  f"{summ['training_seconds'] / 60:.1f} daq, qurilma: {summ['device']}, "
                  f"transfer learning: {'ha' if summ.get('pretrained') else 'yo‘q'}. "
                  f"Grafiklar: `{arch}/training_curves.png`, `{arch}/confusion_val.png`", ""]
        L += metrics_block(read(d / "eval_val.json") or read(d / "val_metrics.json"),
                           f"model o‘qitilmagan (`train.py --config ai/configs/{arch}.yaml`)")

    cmp = read(exp / "model_comparison.json")
    L += ["## 5. Tanlangan model", ""]
    L += [f"{cmp['selected_reason']}. Qoida: {cmp['selection_rule']}.", ""] if cmp else \
        [f"{NA} — `compare_models.py` ishga tushirilmagan.", ""]

    lock = read(exp / "test_lock.json")
    test = None
    if cmp:
        # Tanlangan katalog boshqa kompyuterda (masalan, Colab’da) yozilgan bo‘lishi mumkin — nomi bo‘yicha topiladi
        test = read(exp / Path(str(cmp["selected"])).name / "eval_test.json")
    L += ["## 6. Mustaqil sinov (test) natijalari", ""]
    if lock:
        L += [f"Test to‘plami bir marta, faqat `{lock['checkpoint']}` uchun ishlatilgan ({lock['locked_at']}).", ""]
    L += metrics_block(test, "yakuniy test bajarilmagan (`evaluate.py --split test`)")

    L += ["## 7. `artifacts/model.pt`", ""]
    model_path = art / "model.pt"
    if model_path.is_file():
        try:
            lm = load_checkpoint(model_path)
            L += [f"Mavjud. Arxitektura: {lm.architecture}, versiya: {lm.model_version}, SHA-256: `{lm.sha256}`, "
                  f"sinflar: {lm.class_names}, kirish: {lm.preprocess.input_size}×{lm.preprocess.input_size}, "
                  f"mean={list(lm.preprocess.mean)}, std={list(lm.preprocess.std)}.", ""]
            status = "Backend yuklovchisi tekshiruvidan o‘tdi — server ishga tushganda real tahlil uchun yuklanadi."
        except CheckpointError as e:
            L += [f"Fayl bor, lekin yuklanmaydi: {e.code} — {e.message}", ""]
            status = f"Ulanmagan: {e.code}"
    else:
        L += [f"{NA} — tahlil funksiyasi cheklangan holatda (API `503 MODEL_NOT_READY`).", ""]
        status = "Integratsiya kodi tayyor va testlangan, lekin o‘qitilgan model yo‘qligi sababli real tahlil o‘chirilgan."
    L += ["## 8. Backend integratsiyasi", "", status, ""]

    bench = read(exp / "benchmark.json")
    if bench:
        L += [f"CPU tezligi ({bench['cpu']}, {bench['torch_threads']} oqim): median {bench['median_ms']:.0f} ms, "
              f"P90 {bench['p90_ms']:.0f} ms.", ""]

    L += ["## 9. Cheklovlar", "",
          "- Ehtimolliklar kalibrlanmagan (`calibration_evaluated: false`).",
          "- Model faqat bitta tizzaning frontal (PA) rentgen tasviri uchun o‘qitilgan; proyeksiya avtomatik aniqlanmaydi.",
          "- Natijalar bitta dataset (manba yuqorida) bo‘yicha; boshqa qurilma va populyatsiyalarda tashqi validatsiya qilinmagan.",
          "- Klinik tashxis vositasi emas.", ""]
    out = resolve(args.out) if args.out else exp / "EXPERIMENT_REPORT.md"
    out.write_text("\n".join(L), encoding="utf-8")
    print(f"Hisobot: {out}")


if __name__ == "__main__":
    main()
