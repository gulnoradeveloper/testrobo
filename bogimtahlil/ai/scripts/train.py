"""Modelni o‘qitish (ResNet-18 / EfficientNet-B0).

    python ai/scripts/train.py --config ai/configs/efficientnet_b0.yaml

Har bir epoch uchun train/val loss, accuracy, macro F1, sinflar bo‘yicha recall
`history.csv` ga yoziladi. Eng yaxshi checkpoint faqat validation macro F1 bo‘yicha tanlanadi;
test to‘plami bu skriptda umuman o‘qilmaydi.
"""
from __future__ import annotations

import argparse
import csv
import json
import time

from _common import load_config, pick_device, resolve, set_seed

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader

from kltool import KL_CLASSES
from kltool.architectures import build_model
from kltool.checkpoint import TRAINED, save_checkpoint
from kltool.data import KneeXrayDataset, class_weights, load_manifest
from kltool.metrics import compute_metrics
from kltool.preprocess import DEFAULT_CONFIG


def run_epoch(model, loader, criterion, device, optimizer=None):
    training = optimizer is not None
    model.train(training)
    total_loss, n = 0.0, 0
    preds, targets = [], []
    with torch.set_grad_enabled(training):
        for x, y in loader:
            x, y = x.to(device), torch.as_tensor(y).to(device)
            logits = model(x)
            loss = criterion(logits, y)
            if training:
                optimizer.zero_grad(set_to_none=True)
                loss.backward()
                optimizer.step()
            total_loss += float(loss) * len(y)
            n += len(y)
            preds.append(logits.argmax(1).cpu().numpy())
            targets.append(y.cpu().numpy())
    return total_loss / max(n, 1), np.concatenate(targets), np.concatenate(preds)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", required=True)
    ap.add_argument("--device", default="auto")
    ap.add_argument("--epochs", type=int, help="konfiguratsiyadagi qiymatni almashtirish")
    args = ap.parse_args()

    cfg = load_config(args.config)
    if args.epochs:
        cfg["epochs"] = args.epochs
    set_seed(int(cfg["seed"]))
    device = pick_device(args.device)
    out_dir = resolve(cfg["output_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)

    df = load_manifest(resolve(cfg["manifest"]))
    train_df, val_df = df[df["split"] == "train"], df[df["split"] == "val"]
    if train_df.empty or val_df.empty:
        raise SystemExit("Manifestda train yoki val guruhi bo‘sh — avval prepare_dataset.py ni ishga tushiring")

    gen = torch.Generator().manual_seed(int(cfg["seed"]))
    train_loader = DataLoader(
        KneeXrayDataset(train_df, DEFAULT_CONFIG, augment=True, seed=int(cfg["seed"])),
        batch_size=int(cfg["batch_size"]), shuffle=True, num_workers=int(cfg["num_workers"]), generator=gen,
    )
    val_loader = DataLoader(
        KneeXrayDataset(val_df, DEFAULT_CONFIG, augment=False),
        batch_size=int(cfg["batch_size"]), shuffle=False, num_workers=int(cfg["num_workers"]),
    )

    model = build_model(cfg["architecture"], pretrained=bool(cfg.get("pretrained", True))).to(device)
    weights = torch.tensor(class_weights(train_df["kl_grade"]), device=device)
    criterion = nn.CrossEntropyLoss(weight=weights)
    optimizer = torch.optim.AdamW(model.parameters(), lr=float(cfg["learning_rate"]), weight_decay=float(cfg["weight_decay"]))

    history_path = out_dir / "history.csv"
    fields = ["epoch", "train_loss", "val_loss", "train_accuracy", "val_accuracy", "val_macro_f1", "val_qwk",
              *[f"val_recall_{c}" for c in KL_CLASSES], "epoch_seconds"]
    best_score, best_epoch, patience = -1.0, 0, int(cfg["early_stopping_patience"])
    started = time.time()
    with open(history_path, "w", newline="", encoding="utf-8") as hf:
        writer = csv.DictWriter(hf, fieldnames=fields)
        writer.writeheader()
        for epoch in range(1, int(cfg["epochs"]) + 1):
            t0 = time.time()
            tr_loss, tr_y, tr_p = run_epoch(model, train_loader, criterion, device, optimizer)
            va_loss, va_y, va_p = run_epoch(model, val_loader, criterion, device)
            vm = compute_metrics(va_y, va_p)
            row = {
                "epoch": epoch, "train_loss": tr_loss, "val_loss": va_loss,
                "train_accuracy": float((tr_y == tr_p).mean()), "val_accuracy": vm["accuracy"],
                "val_macro_f1": vm["macro_f1"], "val_qwk": vm["quadratic_weighted_kappa"],
                **{f"val_recall_{c}": vm["per_class"][c]["recall"] for c in KL_CLASSES},
                "epoch_seconds": time.time() - t0,
            }
            writer.writerow(row)
            hf.flush()
            print(json.dumps(row))
            score = vm[cfg.get("selection_metric", "macro_f1")]
            if score > best_score:
                best_score, best_epoch = score, epoch
                save_checkpoint(
                    out_dir / "best.pt", model, cfg["architecture"], cfg["model_version"], DEFAULT_CONFIG,
                    training_status=TRAINED,
                    dataset={"manifest": cfg["manifest"], "n_train": len(train_df), "n_val": len(val_df)},
                    metrics={"validation": vm},
                    training={**cfg, "best_epoch": epoch},
                )
            elif epoch - best_epoch >= patience:
                print(f"Erta to‘xtatish: {patience} epoch davomida yaxshilanish yo‘q")
                break

    summary = {
        "architecture": cfg["architecture"], "best_epoch": best_epoch,
        "best_val_" + cfg.get("selection_metric", "macro_f1"): best_score,
        "training_seconds": time.time() - started, "device": str(device),
    }
    (out_dir / "train_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    from plots import plot_history

    plot_history(history_path, out_dir / "training_curves.png")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
