"""Inference tezligini o‘lchash (TT: CPUda median ≤ 10 s maqsadi).

    python ai/scripts/benchmark.py --checkpoint artifacts/model.pt --image some_knee.png --runs 20

Preprocess + forward + Grad-CAM to‘liq zanjiri o‘lchanadi. Natija experiments/benchmark.json ga yoziladi.
"""
from __future__ import annotations

import argparse
import json
import platform
import statistics
import time

from _common import pick_device, resolve

import torch

from kltool.architectures import gradcam_target_layer
from kltool.checkpoint import load_checkpoint
from kltool.gradcam import GradCAM
from kltool.preprocess import decode_grayscale, preprocess_array


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--checkpoint", required=True)
    ap.add_argument("--image", required=True)
    ap.add_argument("--runs", type=int, default=20)
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--allow-untrained", action="store_true", help="faqat tezlikni o‘lchash uchun")
    ap.add_argument("--out", default="experiments/benchmark.json")
    args = ap.parse_args()

    device = pick_device(args.device)
    lm = load_checkpoint(resolve(args.checkpoint), device=device, allow_untrained=args.allow_untrained)
    cam = GradCAM(lm.model, gradcam_target_layer(lm.model, lm.architecture))
    data = resolve(args.image).read_bytes()
    times = []
    for i in range(args.runs + 1):
        t0 = time.perf_counter()
        x, _ = preprocess_array(decode_grayscale(data), lm.preprocess)
        xt = torch.from_numpy(x)[None].to(device)
        with torch.inference_mode():
            probs = torch.softmax(lm.model(xt), 1)
        cam(xt, int(probs.argmax()))
        if i:  # birinchi (isinish) o‘lchov hisobga olinmaydi
            times.append((time.perf_counter() - t0) * 1000)
    res = {"model_version": lm.model_version, "training_status": lm.training_status, "device": str(device),
           "cpu": platform.processor() or platform.machine(), "torch_threads": torch.get_num_threads(),
           "runs": args.runs, "median_ms": statistics.median(times), "p90_ms": sorted(times)[int(0.9 * len(times)) - 1],
           "min_ms": min(times), "max_ms": max(times)}
    resolve(args.out).parent.mkdir(parents=True, exist_ok=True)
    resolve(args.out).write_text(json.dumps(res, indent=2), encoding="utf-8")
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
