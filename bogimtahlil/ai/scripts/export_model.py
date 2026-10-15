"""Tanlangan modelni test metrikalari bilan birga dasturga eksport qilish.

    python ai/scripts/export_model.py --run experiments/efficientnet_b0 --dataset-name "OAI" \
        --dataset-license "OAI Data Use Agreement" --out artifacts/model.pt

Natija: artifacts/model.pt, artifacts/model.pt.sha256, artifacts/model_card.json
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
    args = ap.parse_args()

    run = resolve(args.run)
    lm = load_checkpoint(run / "best.pt")
    test_path = run / "eval_test.json"
    if not test_path.is_file():
        raise SystemExit("eval_test.json topilmadi — avval evaluate.py --split test ni ishga tushiring")
    test = json.loads(test_path.read_text(encoding="utf-8"))
    metrics = {**lm.metrics, "test": test, "calibration_evaluated": False}
    dataset = {**lm.dataset, "name": args.dataset_name, "license": args.dataset_license, "notes": args.dataset_notes,
               "n_test": test["n_samples"]}
    digest = save_checkpoint(resolve(args.out), lm.model, lm.architecture, lm.model_version, lm.preprocess,
                             training_status=TRAINED, dataset=dataset, metrics=metrics, training=lm.training)
    card = {"model_version": lm.model_version, "architecture": lm.architecture, "sha256": digest,
            "dataset": dataset, "test_metrics": {k: test[k] for k in
            ("accuracy", "balanced_accuracy", "macro_f1", "quadratic_weighted_kappa")}}
    resolve(args.out).with_name("model_card.json").write_text(json.dumps(card, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(card, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
