"""To‘liq tajriba: ajratish → ResNet-18 va EfficientNet-B0 ni o‘qitish → validation baholash → tanlash →
yakuniy test (faqat tanlangan model) → eksport → benchmark → hisobot.

    python ai/scripts/run_experiment.py --manifest data/raw/manifest.csv \
        --dataset-name "Osteoarthritis Initiative (OAI)" --dataset-license "OAI Data Use Agreement"

Har bir qadam alohida skript sifatida ishga tushiriladi; xato bo‘lsa jarayon to‘xtaydi.
Barcha hisobot raqamlari faqat shu jarayonda yaratilgan fayllardan olinadi.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys

from _common import AI_DIR, resolve

SCRIPTS = AI_DIR / "scripts"
CONFIGS = {"resnet18": AI_DIR / "configs" / "resnet18.yaml", "efficientnet_b0": AI_DIR / "configs" / "efficientnet_b0.yaml"}


def step(name: str, *args) -> None:
    print(f"\n=== {name} ===", flush=True)
    r = subprocess.run([sys.executable, *map(str, args)])
    if r.returncode != 0:
        raise SystemExit(f"'{name}' bosqichi xato bilan tugadi (kod {r.returncode})")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest", required=True, help="split’siz manifest (build_oai_manifest.py natijasi)")
    ap.add_argument("--dataset-name", required=True)
    ap.add_argument("--dataset-license", required=True)
    ap.add_argument("--dataset-notes", default="")
    ap.add_argument("--splits-dir", default="data/splits")
    ap.add_argument("--experiments-dir", default="experiments")
    ap.add_argument("--artifacts-dir", default="artifacts")
    ap.add_argument("--epochs", type=int)
    ap.add_argument("--num-workers", type=int)
    ap.add_argument("--keep-existing-split", action="store_true",
                    help="manifestdagi tayyor train/val/test taqsimotidan foydalanish (masalan, Chen 2018 dataseti)")
    ap.add_argument("--no-pretrained", action="store_true", help="faqat smoke-test uchun (transfer learningsiz)")
    ap.add_argument("--benchmark-image", help="tezlikni o‘lchash uchun tasvir (bo‘lmasa test guruhidan birinchisi)")
    args = ap.parse_args()

    if not resolve(args.manifest).is_file():
        raise SystemExit(
            f"Manifest topilmadi: {args.manifest}\n"
            "Avval OAI ma’lumotlaridan manifest yarating (build_oai_manifest.py) — docs/MODEL_OQITISH.md, 1–3-bandlar."
        )
    exp, art, splits = resolve(args.experiments_dir), resolve(args.artifacts_dir), resolve(args.splits_dir)
    manifest = splits / "manifest_split.csv"
    step("1. Ma’lumotlarni tekshirish va bemorlar bo‘yicha ajratish", SCRIPTS / "prepare_dataset.py",
         "--manifest", resolve(args.manifest), "--out", splits,
         *(["--keep-existing-split"] if args.keep_existing_split else []))

    runs = []
    for arch, cfg in CONFIGS.items():
        extra = []
        if args.epochs:
            extra += ["--epochs", args.epochs]
        if args.no_pretrained:
            extra += ["--no-pretrained"]
        if args.num_workers is not None:
            extra += ["--num-workers", args.num_workers]
        step(f"2. O‘qitish: {arch}", SCRIPTS / "train.py", "--config", cfg, "--manifest", manifest,
             "--output-dir", exp / arch, "--artifact-path", art / f"{arch}_best.pt", *extra)
        step(f"3. Validation baholash: {arch}", SCRIPTS / "evaluate.py", "--checkpoint", exp / arch / "best.pt",
             "--manifest", manifest, "--split", "val")
        runs.append(exp / arch)

    step("4. Validation bo‘yicha tanlash", SCRIPTS / "compare_models.py", *runs, "--out", exp / "model_comparison.json")
    selected = resolve(json.loads((exp / "model_comparison.json").read_text(encoding="utf-8"))["selected"])
    step("5. Yakuniy mustaqil test (faqat tanlangan model)", SCRIPTS / "evaluate.py", "--checkpoint",
         selected / "best.pt", "--manifest", manifest, "--split", "test", "--test-lock", exp / "test_lock.json")
    step("6. Eksport: artifacts/model.pt", SCRIPTS / "export_model.py", "--run", selected, "--out", art / "model.pt",
         "--dataset-name", args.dataset_name, "--dataset-license", args.dataset_license,
         "--dataset-notes", args.dataset_notes, "--comparison", exp / "model_comparison.json",
         "--test-lock", exp / "test_lock.json")
    bench_img = args.benchmark_image
    if not bench_img:
        import pandas as pd

        df = pd.read_csv(manifest, dtype=str)
        bench_img = df[df["split"] == "test"]["image_path"].iloc[0]
    step("7. Tezlik o‘lchovi", SCRIPTS / "benchmark.py", "--checkpoint", art / "model.pt", "--image", bench_img,
         "--device", "cpu", "--out", exp / "benchmark.json")
    step("8. Hisobot", SCRIPTS / "make_report.py", "--splits-dir", splits, "--experiments-dir", exp,
         "--artifacts-dir", art)


if __name__ == "__main__":
    main()
