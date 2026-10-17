"""Datasetni tayyorlash: manifestni tekshirish, takrorlarni aniqlash, bemorlar bo‘yicha 70/15/15 ajratish.

    python ai/scripts/prepare_dataset.py --manifest data/raw/manifest.csv --out data/splits

Natija:
    data/splits/manifest_split.csv   — split ustuni qo‘shilgan manifest
    data/splits/dataset_report.json  — tekshiruv, takrorlar, har bir guruhdagi tasvir/bemor/KL0–KL4 soni
Bitta bemor ikki guruhga tushsa, skript xato bilan to‘xtaydi.
OAI ma’lumotlari repozitoriyga joylashtirilmaydi (data/ katalogi .gitignore da).
"""
from __future__ import annotations

import argparse
import json

from _common import resolve

from kltool.data import (
    FRONTAL_VIEWS,
    MANIFEST_COLUMNS,
    check_patient_leakage,
    find_duplicate_images,
    load_manifest,
    patient_split,
    split_summary,
    validate_manifest,
)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--out", default="data/splits")
    ap.add_argument("--val-frac", type=float, default=0.15)
    ap.add_argument("--test-frac", type=float, default=0.15)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--keep-existing-split", action="store_true", help="manifestdagi tayyor split’dan foydalanish")
    args = ap.parse_args()

    df = load_manifest(resolve(args.manifest))
    report = {"validation": validate_manifest(df)}
    if report["validation"]["missing_files"]:
        raise SystemExit("Ba’zi tasvir fayllari topilmadi — manifestni tuzating: " + json.dumps(report, ensure_ascii=False))

    df = df[df["projection"].isin(FRONTAL_VIEWS) & df["kl_grade"].isin(list(range(5)))
            & df["knee_side"].isin(["L", "R"])].copy()
    df["kl_grade"] = df["kl_grade"].astype(int)
    key_dup = df.duplicated(subset=["patient_id", "knee_side", "visit_id"], keep=False)
    df = df[~key_dup].copy()  # bitta tizza/tashrif uchun bir nechta yozuv — noaniq, chiqariladi
    df = find_duplicate_images(df)
    conflicting = df.groupby("image_sha256")["kl_grade"].nunique()
    bad_hashes = set(conflicting[conflicting > 1].index)
    dup_mask = df.duplicated(subset=["image_sha256"], keep="first")
    report["duplicates"] = {
        "ambiguous_knee_visit_records_removed": int(key_dup.sum()),
        "identical_images_removed": int(dup_mask.sum()),
        "identical_images_with_conflicting_labels": len(bad_hashes),
    }
    df = df[~dup_mask & ~df["image_sha256"].isin(bad_hashes)].copy()
    # Bir xil tasvir turli bemorlarda uchrasa (ma’lumot xatosi) — bemor bo‘yicha ajratish buziladi
    cross = df.groupby("image_sha256")["patient_id"].nunique()
    report["duplicates"]["identical_images_across_patients"] = int((cross > 1).sum())

    if args.keep_existing_split and "split" in df.columns and df["split"].notna().all():
        report["split_source"] = "manifestdagi tayyor split"
    else:
        df = patient_split(df, args.val_frac, args.test_frac, args.seed)
        report["split_source"] = (f"bemorlar bo‘yicha, eng yuqori KL bo‘yicha stratifikatsiya, "
                                  f"train/val/test = {1 - args.val_frac - args.test_frac:.2f}/{args.val_frac:.2f}/"
                                  f"{args.test_frac:.2f}, seed={args.seed}")

    verified = bool(df["patient_id_verified"].astype(str).str.lower().eq("true").all()) \
        if "patient_id_verified" in df.columns else True
    report["patient_ids_verified"] = verified
    if not verified:
        report["patient_ids_note"] = ("Datasetda bemor identifikatorlari yo‘q — bemorlar bo‘yicha ajratishni tekshirib "
                                      "bo‘lmaydi; bitta bemorning tasvirlari turli guruhlarga tushgan bo‘lishi mumkin.")
    leaks = check_patient_leakage(df)
    report["patient_leakage"] = {"n_patients_in_multiple_splits": len(leaks)}
    if leaks:
        raise SystemExit(f"Bemorlar bir nechta guruhga tushib qolgan: {len(leaks)} ta — ajratishni tuzating")

    report["totals"] = {"images": int(len(df)), "patients": int(df["patient_id"].nunique()),
                        "sources": df["dataset_source"].value_counts().to_dict()}
    report["splits"] = split_summary(df)

    out = resolve(args.out)
    out.mkdir(parents=True, exist_ok=True)
    cols = [c for c in MANIFEST_COLUMNS] + [c for c in df.columns if c not in MANIFEST_COLUMNS]
    df[cols].to_csv(out / "manifest_split.csv", index=False)
    (out / "dataset_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
