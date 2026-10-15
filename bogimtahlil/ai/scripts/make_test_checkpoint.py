"""O‘QITILMAGAN test checkpointi yaratish — faqat dastur zanjirini texnik sinash uchun.

    python ai/scripts/make_test_checkpoint.py --out /tmp/fixture.pt --arch resnet18

Checkpoint "untrained-test-fixture" deb belgilanadi; backend uni faqat BT_ALLOW_UNTRAINED_MODEL=true
bo‘lganda yuklaydi va barcha natijalarda “o‘qitilmagan test modeli” ogohlantirishini ko‘rsatadi.
"""
from __future__ import annotations

import argparse

from _common import resolve

import torch

from kltool.architectures import SUPPORTED_ARCHITECTURES, build_model
from kltool.checkpoint import UNTRAINED_FIXTURE, save_checkpoint
from kltool.preprocess import DEFAULT_CONFIG


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", required=True)
    ap.add_argument("--arch", default="resnet18", choices=SUPPORTED_ARCHITECTURES)
    args = ap.parse_args()
    torch.manual_seed(0)
    digest = save_checkpoint(resolve(args.out), build_model(args.arch), args.arch, "test-fixture-0.0.0", DEFAULT_CONFIG,
                             training_status=UNTRAINED_FIXTURE, dataset={"name": "yo‘q (o‘qitilmagan test checkpointi)"})
    print(f"{args.out}  sha256={digest}  (O‘QITILMAGAN — faqat texnik sinov uchun)")


if __name__ == "__main__":
    main()
