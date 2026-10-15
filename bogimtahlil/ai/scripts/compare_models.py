"""Modellarni FAQAT validation natijasi bo‘yicha taqqoslash va tanlash (test ishlatilmaydi).

    python ai/scripts/compare_models.py experiments/resnet18 experiments/efficientnet_b0

Adolatli taqqoslash sharti tekshiriladi: barcha modellar bir xil manifest (split) va bir xil sinflar tartibida
o‘qitilgan bo‘lishi kerak. Natija: experiments/model_comparison.json va .md
"""
from __future__ import annotations

import argparse
import json

from _common import resolve

from kltool import KL_CLASSES
from kltool.checkpoint import load_checkpoint

KEYS = ("accuracy", "balanced_accuracy", "macro_precision", "macro_recall", "macro_f1", "quadratic_weighted_kappa")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("runs", nargs="+")
    ap.add_argument("--metric", default="macro_f1")
    ap.add_argument("--tie-breaker", default="quadratic_weighted_kappa")
    ap.add_argument("--out", default="experiments/model_comparison.json")
    args = ap.parse_args()

    rows, manifests, sizes = [], set(), set()
    for run in args.runs:
        d = resolve(run)
        vm = json.loads((d / "val_metrics.json").read_text(encoding="utf-8"))
        summary = json.loads((d / "train_summary.json").read_text(encoding="utf-8"))
        lm = load_checkpoint(d / "best.pt")
        if lm.class_names != list(KL_CLASSES):
            raise SystemExit(f"{run}: sinflar tartibi farq qiladi")
        manifests.add(lm.dataset.get("manifest"))
        sizes.add((lm.dataset.get("n_train"), lm.dataset.get("n_val")))
        rows.append({"run": run, "architecture": lm.architecture, "model_version": lm.model_version,
                     "best_epoch": summary["best_epoch"], "epochs_run": summary.get("epochs_run"),
                     "training_seconds": round(summary["training_seconds"], 1), "checkpoint_sha256": lm.sha256,
                     "val": {k: vm[k] for k in KEYS},
                     "val_recall": {c: vm["per_class"][c]["recall"] for c in KL_CLASSES}})
    if len(manifests) != 1 or len(sizes) != 1:
        raise SystemExit(f"Modellar turli ma’lumotlar taqsimotida o‘qitilgan: {manifests} {sizes} — taqqoslash adolatsiz")

    rows.sort(key=lambda r: (r["val"][args.metric], r["val"][args.tie_breaker]), reverse=True)
    best = rows[0]
    result = {
        "selection_rule": f"validation {args.metric} (teng bo‘lsa: {args.tie_breaker}); test to‘plami ishlatilmagan",
        "manifest": manifests.pop(), "ranking": rows, "selected": best["run"],
        "selected_reason": f"{best['architecture']}: validation {args.metric} = {best['val'][args.metric]:.4f} — eng yuqori",
    }
    out = resolve(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = ["| Model | " + " | ".join(KEYS) + " | " + " | ".join(f"Recall {c}" for c in KL_CLASSES) + " |",
             "|" + "---|" * (1 + len(KEYS) + len(KL_CLASSES))]
    for r in rows:
        lines.append(f"| {r['architecture']} | " + " | ".join(f"{r['val'][k]:.4f}" for k in KEYS) + " | "
                     + " | ".join(f"{r['val_recall'][c]:.3f}" for c in KL_CLASSES) + " |")
    md = (f"# Modellarni taqqoslash (validation)\n\nTanlash qoidasi: {result['selection_rule']}\n\n" + "\n".join(lines)
          + f"\n\n**Tanlangan:** {result['selected_reason']}\n")
    out.with_suffix(".md").write_text(md, encoding="utf-8")
    print(md)


if __name__ == "__main__":
    main()
