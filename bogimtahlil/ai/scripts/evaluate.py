"""Checkpointni ma’lum guruhda baholash.

    python ai/scripts/evaluate.py --checkpoint experiments/resnet18/best.pt --split val
    python ai/scripts/evaluate.py --checkpoint experiments/efficientnet_b0/best.pt --split test

Natija: <checkpoint katalogi>/eval_<split>.json, confusion_<split>.png, predictions_<split>.csv

Yakuniy test himoyasi: test guruhi faqat BITTA (validation bo‘yicha tanlangan) checkpoint uchun baholanadi.
Birinchi test bahosi experiments/test_lock.json ga yoziladi; boshqa checkpointni test qilishga urinish rad etiladi.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone

from _common import pick_device, resolve

import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader

from kltool import KL_CLASSES
from kltool.checkpoint import load_checkpoint
from kltool.data import KneeXrayDataset, load_manifest
from kltool.metrics import compute_metrics
from plots import plot_confusion


def check_test_lock(lock_path, sha: str, checkpoint: str) -> None:
    if lock_path.is_file():
        lock = json.loads(lock_path.read_text(encoding="utf-8"))
        if lock["checkpoint_sha256"] != sha:
            raise SystemExit(
                f"Test to‘plami allaqachon boshqa model uchun ishlatilgan ({lock['checkpoint']}). Test natijasiga qarab "
                "modelni qayta tanlash taqiqlanadi. Tanlov validation bo‘yicha: compare_models.py."
            )
        return
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_text(json.dumps({"checkpoint": checkpoint, "checkpoint_sha256": sha,
                                     "locked_at": datetime.now(timezone.utc).isoformat()}, indent=2), encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--checkpoint", required=True)
    ap.add_argument("--manifest", default="data/splits/manifest_split.csv")
    ap.add_argument("--split", default="val", choices=["train", "val", "test"])
    ap.add_argument("--batch-size", type=int, default=32)
    ap.add_argument("--device", default="auto")
    ap.add_argument("--test-lock", default="experiments/test_lock.json")
    args = ap.parse_args()

    device = pick_device(args.device)
    ckpt_path = resolve(args.checkpoint)
    lm = load_checkpoint(ckpt_path, device=device)
    if args.split == "test":
        check_test_lock(resolve(args.test_lock), lm.sha256, str(args.checkpoint))
    df = load_manifest(resolve(args.manifest))
    part = df[df["split"] == args.split]
    if part.empty:
        raise SystemExit(f"Manifestda '{args.split}' guruhi bo‘sh")
    loader = DataLoader(KneeXrayDataset(part, lm.preprocess), batch_size=args.batch_size, shuffle=False)

    probs, targets = [], []
    with torch.inference_mode():
        for x, y in loader:
            probs.append(torch.softmax(lm.model(x.to(device)), 1).cpu().numpy())
            targets.append(np.asarray(y))
    p = np.concatenate(probs)
    y = np.concatenate(targets)
    m = compute_metrics(y, p.argmax(1))
    m.update(split=args.split, checkpoint_sha256=lm.sha256, model_version=lm.model_version,
             architecture=lm.architecture, n_patients=int(part["patient_id"].nunique()))

    out_dir = ckpt_path.parent
    (out_dir / f"eval_{args.split}.json").write_text(json.dumps(m, ensure_ascii=False, indent=2), encoding="utf-8")
    pred = part[["patient_id", "knee_side", "visit_id", "kl_grade"]].copy()
    pred["predicted"] = p.argmax(1)
    for i, c in enumerate(KL_CLASSES):
        pred[f"p_{c}"] = p[:, i].round(5)
    pred.to_csv(out_dir / f"predictions_{args.split}.csv", index=False)
    plot_confusion(m["confusion_matrix"], KL_CLASSES, out_dir / f"confusion_{args.split}.png",
                   f"{lm.model_version} — {args.split}")
    print(json.dumps({k: m[k] for k in ("accuracy", "balanced_accuracy", "macro_precision", "macro_recall", "macro_f1",
                                        "quadratic_weighted_kappa")}, indent=2))
    print("Recall:", {c: round(v["recall"], 3) for c, v in m["per_class"].items()})


if __name__ == "__main__":
    main()
