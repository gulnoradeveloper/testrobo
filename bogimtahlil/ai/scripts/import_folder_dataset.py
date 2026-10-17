"""Sinflar bo‘yicha papkalarga ajratilgan datasetdan manifest yaratish.

Kutilgan tuzilma:  <root>/<split>/<grade>/<fayl>.png   (split: train|val|test, grade: 0..4)
Fayl nomidan bemor ID olinadigan regex berilishi mumkin (--patient-regex).

DIQQAT: agar datasetda bemor identifikatori bo‘lmasa, har bir tasvir alohida "bemor" deb
belgilanadi va bemorlar bo‘yicha ajratishni TEKSHIRIB BO‘LMAYDI. Bu holat dataset hisobotida
va model kartasida cheklov sifatida ko‘rsatilishi shart.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd

from _common import resolve

EXTS = {".png", ".jpg", ".jpeg"}
SPLIT_DIRS = {"train": "train", "val": "val", "valid": "val", "validation": "val", "test": "test"}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", required=True)
    ap.add_argument("--out", default="data/raw/manifest.csv")
    ap.add_argument("--patient-regex", help="masalan: '^(\\d{7})' — fayl nomidan bemor ID")
    ap.add_argument("--side-regex", help="masalan: '_(L|R)'")
    ap.add_argument("--view", default="PA")
    ap.add_argument("--source", required=True, help="ma’lumot manbasi nomi (masalan, dataset nomi va versiyasi)")
    ap.add_argument("--keep-split", action="store_true", help="papkadagi split'ni saqlash")
    ap.add_argument("--path-contains", help="faqat yo‘lida shu matn bor fayllar (masalan, kneeKL224)")
    args = ap.parse_args()

    root = resolve(args.root)
    rows = []
    for f in sorted(root.rglob("*")):
        if f.suffix.lower() not in EXTS:
            continue
        grade = f.parent.name
        if not grade.isdigit() or int(grade) not in range(5):
            continue
        if args.path_contains and args.path_contains not in f.as_posix():
            continue
        split_dir = f.parent.parent.name.lower()
        if args.keep_split and split_dir not in SPLIT_DIRS:
            continue  # masalan, auto_test — o‘qitish/baholash taqsimotiga kirmaydi
        pid, side = None, "L"
        if args.patient_regex and (m := re.search(args.patient_regex, f.name)):
            pid = m.group(1)
        if args.side_regex and (m := re.search(args.side_regex, f.name)):
            side = m.group(1).upper()
        rows.append({
            "image_path": str(f), "patient_id": pid or f"img-{f.stem}-{len(rows)}", "knee_side": side,
            "visit_id": f"{f.parent.parent.name}-{len(rows)}", "projection": args.view, "kl_grade": int(grade),
            "dataset_source": args.source,
            **({"split": SPLIT_DIRS[split_dir]} if args.keep_split else {}),
            "patient_id_verified": bool(pid),
        })
    out = resolve(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(out, index=False)
    print(f"{len(rows)} ta yozuv → {out}")


if __name__ == "__main__":
    main()
