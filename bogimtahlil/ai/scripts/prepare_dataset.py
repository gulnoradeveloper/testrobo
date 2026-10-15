"""Datasetni tayyorlash: manifestni tekshirish, takrorlarni aniqlash, bemorlar bo‘yicha 70/15/15 ajratish.

Ishlatish:
    python ai/scripts/prepare_dataset.py --manifest data/raw/manifest.csv --out data/splits

Natija:
    data/splits/manifest_split.csv   — split ustuni qo‘shilgan manifest
    data/splits/dataset_report.json  — tekshiruv, takrorlar, sinflar taqsimoti
OAI ma’lumotlari repozitoriyga joylashtirilmaydi (data/ katalogi .gitignore da).
"""
from __future__ import annotations

import argparse
import json

from _common import resolve

from kltool.data import (
    FRONTAL_VIEWS,
    check_patient_leakage,
    class_distribution,
    find_duplicate_images,
    load_manifest,
    patient_split,
    validate_manifest,
)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--out", default="data/splits")
    ap.add_argument("--val-frac", type=float, default=0.15)
    ap.add_argument("--test-frac", type=float, default=0.15)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    df = load_manifest(resolve(args.manifest))
    report = {"validation": validate_manifest(df)}
    if report["validation"]["missing_files"]:
        raise SystemExit("Ba’zi tasvir fayllari topilmadi — manifestni tuzating: " + json.dumps(report, ensure_ascii=False))

    df = df[df["view"].str.upper().isin(FRONTAL_VIEWS) & df["kl_grade"].isin(range(5))].copy()
    df = find_duplicate_images(df)
    dup_mask = df.duplicated(subset=["image_sha256"], keep="first")
    conflicting = df.groupby("image_sha256")["kl_grade"].nunique()
    report["duplicates"] = {
        "removed_identical_images": int(dup_mask.sum()),
        "identical_images_with_conflicting_labels": int((conflicting > 1).sum()),
    }
    df = df[~dup_mask].copy()
    # Bir xil tasvirga turli yorliq berilgan bo‘lsa — ishonchsiz, chiqariladi
    bad_hashes = set(conflicting[conflicting > 1].index)
    df = df[~df["image_sha256"].isin(bad_hashes)].copy()

    if "split" in df.columns and df["split"].notna().all():
        report["split_source"] = "manifestdagi tayyor split"
    else:
        df = patient_split(df, args.val_frac, args.test_frac, args.seed)
        report["split_source"] = f"bemorlar bo‘yicha stratifikatsiyalangan, seed={args.seed}"

    leaks = check_patient_leakage(df)
    report["patient_leakage"] = {"n_patients_in_multiple_splits": len(leaks)}
    if leaks:
        raise SystemExit(f"Bemorlar bir nechta guruhga tushib qolgan: {len(leaks)} ta — ajratishni tuzating")

    report["class_distribution"] = class_distribution(df)
    report["patients_per_split"] = {s: int(p["patient_id"].nunique()) for s, p in df.groupby("split")}

    out = resolve(args.out)
    out.mkdir(parents=True, exist_ok=True)
    df.to_csv(out / "manifest_split.csv", index=False)
    (out / "dataset_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
