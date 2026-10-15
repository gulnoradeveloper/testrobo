"""Checkpointni ma’lum guruhda baholash (odatda yakuniy test).

    python ai/scripts/evaluate.py --checkpoint experiments/efficientnet_b0/best.pt --split test

Yakuniy test faqat model tanlangandan keyin bir marta ishga tushiriladi.
Natija: <checkpoint katalogi>/eval_<split>.json va confusion_<split>.png
"""
from __future__ import annotations

import argparse
import json

from _common import pick_device, resolve

import numpy as np
import torch
from torch.utils.data import DataLoader

from kltool import KL_CLASSES
from kltool.checkpoint import load_checkpoint
from kltool.data import KneeXrayDataset, load_manifest
from kltool.metrics import compute_metrics
from plots import plot_confusion


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--checkpoint", required=True)
    ap.add_argument("--manifest", default="data/splits/manifest_split.csv")
    ap.add_argument("--split", default="test", choices=["train", "val", "test"])
    ap.add_argument("--batch-size", type=int, default=32)
    ap.add_argument("--device", default="auto")
    args = ap.parse_args()

    device = pick_device(args.device)
    ckpt_path = resolve(args.checkpoint)
    lm = load_checkpoint(ckpt_path, device=device)
    df = load_manifest(resolve(args.manifest))
    part = df[df["split"] == args.split]
    loader = DataLoader(KneeXrayDataset(part, lm.preprocess), batch_size=args.batch_size, shuffle=False)

    probs, targets = [], []
    with torch.inference_mode():
        for x, y in loader:
            probs.append(torch.softmax(lm.model(x.to(device)), 1).cpu().numpy())
            targets.append(np.asarray(y))
    p = np.concatenate(probs)
    y = np.concatenate(targets)
    m = compute_metrics(y, p.argmax(1))
    m["split"] = args.split
    m["checkpoint_sha256"] = lm.sha256
    m["model_version"] = lm.model_version

    out_dir = ckpt_path.parent
    (out_dir / f"eval_{args.split}.json").write_text(json.dumps(m, ensure_ascii=False, indent=2), encoding="utf-8")
    plot_confusion(m["confusion_matrix"], KL_CLASSES, out_dir / f"confusion_{args.split}.png",
                   f"{lm.model_version} — {args.split}")
    print(json.dumps({k: m[k] for k in ("accuracy", "balanced_accuracy", "macro_f1", "quadratic_weighted_kappa")}, indent=2))


if __name__ == "__main__":
    main()
