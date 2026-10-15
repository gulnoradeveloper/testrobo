"""Tanlangan modelni yakuniy test metrikalari bilan dasturga eksport qilish (backend yuklovchisiga mos format).

    python ai/scripts/export_model.py --run experiments/efficientnet_b0 \
        --dataset-name "Osteoarthritis Initiative (OAI)" --dataset-license "OAI Data Use Agreement" \
        --out artifacts/model.pt

Checkpointda saqlanadi: arxitektura, sinflar tartibi, tasvir o‘lchami va me’yorlashtirish (preprocess), model
versiyasi, dataset ma’lumoti, validation va test metrikalari, tanlash sababi.
SHA-256 — artifacts/model.pt.sha256 va model_card.json da (fayl o‘z hashini o‘zida saqlay olmaydi).
"""
from __future__ import annotations

import argparse
import json

from _common import resolve

from kltool.checkpoint import TRAINED, load_checkpoint, save_checkpoint


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run", required=True)
    ap.add_argument("--out", default="artifacts/model.pt")
    ap.add_argument("--dataset-name", required=True)
    ap.add_argument("--dataset-license", required=True)
    ap.add_argument("--dataset-notes", default="")
    ap.add_argument("--comparison", default="experiments/model_comparison.json")
    ap.add_argument("--test-lock", default="experiments/test_lock.json")
    args = ap.parse_args()

    run = resolve(args.run)
    lm = load_checkpoint(run / "best.pt")
    test_path = run / "eval_test.json"
    if not test_path.is_file():
        raise SystemExit("eval_test.json topilmadi — avval evaluate.py --split test ni ishga tushiring")
    test = json.loads(test_path.read_text(encoding="utf-8"))
    if test["checkpoint_sha256"] != lm.sha256:
        raise SystemExit("eval_test.json boshqa checkpointga tegishli")
    lock = resolve(args.test_lock)
    if lock.is_file() and json.loads(lock.read_text())["checkpoint_sha256"] != lm.sha256:
        raise SystemExit("Bu checkpoint validation bo‘yicha tanlangan va test qilingan model emas (test_lock.json)")
    selection = {}
    if resolve(args.comparison).is_file():
        cmp = json.loads(resolve(args.comparison).read_text(encoding="utf-8"))
        selection = {"rule": cmp["selection_rule"], "reason": cmp["selected_reason"],
                     "candidates": [{"architecture": r["architecture"], "val_macro_f1": r["val"]["macro_f1"]}
                                    for r in cmp["ranking"]]}
    val = json.loads((run / "val_metrics.json").read_text(encoding="utf-8")) if (run / "val_metrics.json").is_file() \
        else lm.metrics.get("validation", {})
    metrics = {"validation": val, "test": test, "selection": selection, "calibration_evaluated": False}
    dataset = {**lm.dataset, "name": args.dataset_name, "license": args.dataset_license, "notes": args.dataset_notes,
               "n_test": test["n_samples"], "n_test_patients": test.get("n_patients")}
    out = resolve(args.out)
    digest = save_checkpoint(out, lm.model, lm.architecture, lm.model_version, lm.preprocess,
                             training_status=TRAINED, dataset=dataset, metrics=metrics, training=lm.training)
    load_checkpoint(out)  # backend yuklovchisi bilan aynan bir xil tekshiruvdan o‘tkazish
    card = {"model_version": lm.model_version, "architecture": lm.architecture, "sha256": digest,
            "class_names": lm.class_names, "input_size": lm.preprocess.input_size,
            "normalization": {"mean": list(lm.preprocess.mean), "std": list(lm.preprocess.std)},
            "preprocess_version": lm.preprocess.version, "dataset": dataset, "selection": selection,
            "test_metrics": {k: test[k] for k in ("accuracy", "balanced_accuracy", "macro_precision", "macro_recall",
                                                  "macro_f1", "quadratic_weighted_kappa")},
            "test_recall": {c: v["recall"] for c, v in test["per_class"].items()},
            "calibration_evaluated": False}
    out.with_name("model_card.json").write_text(json.dumps(card, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(card, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
