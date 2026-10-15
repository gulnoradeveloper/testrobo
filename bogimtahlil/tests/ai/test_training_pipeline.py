"""Training → evaluate → export skriptlarining uchidan-uchiga smoke testi.

Sintetik (rentgen bo‘lmagan) mayda tasvirlarda 1 epoch bajariladi — maqsad faqat skriptlar
ishlashini va artefaktlar to‘g‘ri yaratilishini tekshirish. Olingan model hech qayerda ishlatilmaydi.
"""
import csv
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "ai" / "scripts"


def run(*args):
    r = subprocess.run([sys.executable, *map(str, args)], cwd=ROOT, capture_output=True, text=True, timeout=600)
    assert r.returncode == 0, r.stderr[-2000:]
    return r.stdout


def test_pipeline_end_to_end(tmp_path):
    rng = np.random.default_rng(0)
    rows = []
    (tmp_path / "img").mkdir()
    for p in range(30):
        for side in "LR":
            g = int(rng.integers(0, 5))
            f = tmp_path / "img" / f"{p}_{side}.png"
            Image.fromarray((60 + 30 * g + rng.normal(0, 10, (160, 160))).clip(0, 255).astype(np.uint8)).save(f)
            rows.append(dict(image_path=str(f), patient_id=f"P{p}", knee_side=side, projection="PA", visit_id="V00",
                             kl_grade=g, dataset_source="sintetik"))
    with open(tmp_path / "m.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)

    run(SCRIPTS / "prepare_dataset.py", "--manifest", tmp_path / "m.csv", "--out", tmp_path / "splits")
    report = json.loads((tmp_path / "splits" / "dataset_report.json").read_text())
    assert report["patient_leakage"]["n_patients_in_multiple_splits"] == 0

    cfg = tmp_path / "cfg.yaml"
    cfg.write_text(
        f"architecture: resnet18\nmodel_version: smoke\nmanifest: {tmp_path / 'splits' / 'manifest_split.csv'}\n"
        f"output_dir: {tmp_path / 'run'}\npretrained: false\nepochs: 1\nbatch_size: 16\nlearning_rate: 0.0001\n"
        "weight_decay: 0.01\nearly_stopping_patience: 7\nselection_metric: macro_f1\nseed: 42\nnum_workers: 0\n"
    )
    run(SCRIPTS / "train.py", "--config", cfg)
    run_dir = tmp_path / "run"
    for f in ("best.pt", "history.csv", "train_summary.json", "training_curves.png"):
        assert (run_dir / f).is_file(), f
    lock = tmp_path / "test_lock.json"
    run(SCRIPTS / "evaluate.py", "--checkpoint", run_dir / "best.pt", "--manifest",
        tmp_path / "splits" / "manifest_split.csv", "--split", "test", "--test-lock", lock)
    assert lock.is_file()
    ev = json.loads((run_dir / "eval_test.json").read_text())
    assert {"accuracy", "balanced_accuracy", "macro_f1", "quadratic_weighted_kappa", "confusion_matrix"} <= set(ev)
    assert (run_dir / "confusion_test.png").is_file()
    run(SCRIPTS / "export_model.py", "--run", run_dir, "--out", tmp_path / "out" / "model.pt",
        "--dataset-name", "sintetik", "--dataset-license", "test", "--test-lock", lock,
        "--comparison", tmp_path / "yoq.json")

    # Test to‘plamini boshqa checkpoint uchun qayta ishlatish taqiqlangan
    import torch

    from kltool.architectures import build_model
    from kltool.checkpoint import save_checkpoint
    from kltool.preprocess import DEFAULT_CONFIG

    torch.manual_seed(1)
    save_checkpoint(tmp_path / "other.pt", build_model("resnet18"), "resnet18", "other", DEFAULT_CONFIG)
    r = subprocess.run([sys.executable, str(SCRIPTS / "evaluate.py"), "--checkpoint", str(tmp_path / "other.pt"),
                        "--manifest", str(tmp_path / "splits" / "manifest_split.csv"), "--split", "test",
                        "--test-lock", str(lock)], cwd=ROOT, capture_output=True, text=True)
    assert r.returncode != 0 and "qayta tanlash taqiqlanadi" in r.stderr

    from kltool.checkpoint import load_checkpoint

    lm = load_checkpoint(tmp_path / "out" / "model.pt")
    assert lm.metrics["test"]["n_samples"] == ev["n_samples"]
    assert lm.metrics["calibration_evaluated"] is False
    assert (tmp_path / "out" / "model_card.json").is_file()
