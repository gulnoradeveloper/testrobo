"""OAI yorliqlari + tasvir indeksidan manifest yaratish.

    python ai/scripts/build_oai_manifest.py \
        --labels data/raw/oai/kXR_SQ_BU00.txt data/raw/oai/kXR_SQ_BU01.txt ... \
        --image-index data/raw/knee_crops/index.csv \
        --out data/raw/manifest.csv

Natija: manifest.csv (image_path, patient_id, knee_side, visit_id, projection, kl_grade, dataset_source, ...)
va manifest_report.json (har bir bosqichda nechta yozuv chiqarilgani va nima uchun).
"""
from __future__ import annotations

import argparse
import json

import pandas as pd

from _common import AI_DIR, resolve

from kltool.oai import link_images_to_labels, load_config, read_image_index, read_kl_labels, resolve_duplicate_reads


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--labels", nargs="+", required=True, help="kXR_SQ_BU## fayllari")
    ap.add_argument("--image-index", required=True)
    ap.add_argument("--config", default=str(AI_DIR / "configs" / "oai_columns.yaml"))
    ap.add_argument("--out", default="data/raw/manifest.csv")
    ap.add_argument("--source", default="OAI", help="dataset_source ustuni qiymati")
    ap.add_argument("--allow-unverified", action="store_true",
                    help="ustun nomlari hujjat bilan solishtirilmagan bo‘lsa ham ishlash (faqat sinov uchun)")
    args = ap.parse_args()

    for f in [*args.labels, args.image_index]:
        if not resolve(f).is_file():
            raise SystemExit(f"Fayl topilmadi: {f} — yo‘lni tekshiring (docs/MODEL_OQITISH.md)")
    cfg = load_config(resolve(args.config))
    if not cfg.get("verified") and not args.allow_unverified:
        raise SystemExit(
            "configs/oai_columns.yaml dagi ustun nomlari OAI data dictionary bilan hali solishtirilmagan (verified: false). "
            "Solishtirib, verified: true qiling."
        )
    parts, file_stats = [], []
    for f in args.labels:
        df, st = read_kl_labels(resolve(f), cfg)
        parts.append(df)
        file_stats.append(st)
    labels = pd.concat(parts, ignore_index=True)
    labels, dup_stats = resolve_duplicate_reads(labels, cfg.get("duplicate_policy", "agree_or_drop"),
                                                cfg.get("read_project_priority"))
    images = read_image_index(resolve(args.image_index), cfg)
    manifest, link_stats = link_images_to_labels(images, labels, source=args.source)

    out = resolve(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    manifest.to_csv(out, index=False)
    report = {"column_mapping_verified": bool(cfg.get("verified")), "label_files": file_stats,
              "duplicate_reads": dup_stats, "linking": link_stats,
              "patients": int(manifest["patient_id"].nunique()), "images": int(len(manifest))}
    out.with_name("manifest_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
