"""Modellarni validation natijasi bo‘yicha taqqoslash (test ishlatilmaydi).

    python ai/scripts/compare_models.py experiments/resnet18 experiments/efficientnet_b0
"""
from __future__ import annotations

import argparse
import json

from _common import resolve


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("runs", nargs="+")
    ap.add_argument("--metric", default="macro_f1")
    ap.add_argument("--out", default="experiments/model_comparison.json")
    args = ap.parse_args()

    rows = []
    for run in args.runs:
        summary = json.loads((resolve(run) / "train_summary.json").read_text(encoding="utf-8"))
        rows.append({"run": run, "architecture": summary["architecture"],
                     "best_epoch": summary["best_epoch"], "val_score": summary[f"best_val_{args.metric}"]})
    rows.sort(key=lambda r: r["val_score"], reverse=True)
    result = {"selection_metric": f"validation {args.metric}", "ranking": rows, "selected": rows[0]["run"]}
    resolve(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
