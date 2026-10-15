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
import shutil
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


def make_model(cfg: dict) -> nn.Module:
    """Transfer learning: ImageNet vaznlari yuklanadi, oxirgi qatlam 5 sinfga almashtiriladi.

    `pretrained_weights` — oldindan yuklab olingan torchvision vaznlari fayli (internetsiz muhit uchun).
    Vaznlarni olish imkoni bo‘lmasa, o‘qitish TO‘XTATILADI — tasodifiy vaznlardan jimgina boshlanmaydi.
    """
    arch = cfg["architecture"]
    local = cfg.get("pretrained_weights")
    if local:
        model = build_model(arch, pretrained=False)
        state = torch.load(resolve(local), map_location="cpu", weights_only=True)
        state = {k: v for k, v in state.items() if not k.startswith(("fc.", "classifier."))}
        missing, unexpected = model.load_state_dict(state, strict=False)
        head = [k for k in missing if not k.startswith(("fc.", "classifier."))]
        if head or unexpected:
            raise SystemExit(f"ImageNet vaznlari arxitekturaga mos emas: missing={head[:5]}, unexpected={unexpected[:5]}")
        return model
    if cfg.get("pretrained", True):
        try:
            return build_model(arch, pretrained=True)
        except Exception as exc:
            raise SystemExit(
                f"ImageNet vaznlarini yuklab bo‘lmadi ({type(exc).__name__}). Internetga ulaning yoki vaznlar faylini "
                "konfiguratsiyadagi `pretrained_weights` orqali ko‘rsating. Transfer learningsiz o‘qitish uchun "
                "`pretrained: false` ni ataylab belgilang."
            ) from exc
    return build_model(arch, pretrained=False)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", required=True)
    ap.add_argument("--device", default="auto")
    ap.add_argument("--epochs", type=int, help="konfiguratsiyadagi qiymatni almashtirish")
    ap.add_argument("--manifest", help="konfiguratsiyadagi manifestni almashtirish")
    ap.add_argument("--output-dir", help="konfiguratsiyadagi output_dir ni almashtirish")
    ap.add_argument("--artifact-path", help="konfiguratsiyadagi artifact_path ni almashtirish")
    ap.add_argument("--num-workers", type=int)
    ap.add_argument("--no-pretrained", action="store_true",
                    help="transfer learningsiz (tasodifiy vaznlardan) — faqat smoke-test uchun; hisobotda ko‘rsatiladi")
    args = ap.parse_args()

    cfg = load_config(args.config)
    for key, val in (("epochs", args.epochs), ("manifest", args.manifest), ("output_dir", args.output_dir),
                     ("artifact_path", args.artifact_path), ("num_workers", args.num_workers)):
        if val is not None:
            cfg[key] = val
    if args.no_pretrained:
        cfg["pretrained"], cfg["pretrained_weights"] = False, None
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

    model = make_model(cfg).to(device)
    weights = torch.tensor(class_weights(train_df["kl_grade"]), device=device)
    criterion = nn.CrossEntropyLoss(weight=weights)
    optimizer = torch.optim.AdamW(model.parameters(), lr=float(cfg["learning_rate"]), weight_decay=float(cfg["weight_decay"]))

    history_path = out_dir / "history.csv"
    fields = ["epoch", "train_loss", "val_loss", "train_accuracy", "val_accuracy", "val_balanced_accuracy",
              "val_macro_precision", "val_macro_recall", "val_macro_f1", "val_qwk",
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
                "val_balanced_accuracy": vm["balanced_accuracy"], "val_macro_precision": vm["macro_precision"],
                "val_macro_recall": vm["macro_recall"],
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
                (out_dir / "val_metrics.json").write_text(json.dumps({**vm, "epoch": epoch, "split": "val"},
                                                                     ensure_ascii=False, indent=2), encoding="utf-8")
                save_checkpoint(
                    out_dir / "best.pt", model, cfg["architecture"], cfg["model_version"], DEFAULT_CONFIG,
                    training_status=TRAINED,
                    dataset={"manifest": cfg["manifest"], "n_train": len(train_df), "n_val": len(val_df),
                             "n_train_patients": int(train_df["patient_id"].nunique()),
                             "n_val_patients": int(val_df["patient_id"].nunique()),
                             "sources": sorted(train_df["dataset_source"].dropna().unique().tolist())},
                    metrics={"validation": vm},
                    training={**cfg, "best_epoch": epoch},
                )
            elif epoch - best_epoch >= patience:
                print(f"Erta to‘xtatish: {patience} epoch davomida yaxshilanish yo‘q")
                break

    if cfg.get("artifact_path"):
        dst = resolve(cfg["artifact_path"])
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(out_dir / "best.pt", dst)
        shutil.copy2(out_dir / "best.pt.sha256", dst.with_suffix(dst.suffix + ".sha256"))
        sha_line = dst.with_suffix(dst.suffix + ".sha256").read_text().split()[0]
        dst.with_suffix(dst.suffix + ".sha256").write_text(f"{sha_line}  {dst.name}\n", encoding="utf-8")

    summary = {
        "architecture": cfg["architecture"], "best_epoch": best_epoch, "epochs_run": epoch,
        "pretrained": bool(cfg.get("pretrained_weights") or cfg.get("pretrained", True)),
        "best_val_" + cfg.get("selection_metric", "macro_f1"): best_score,
        "training_seconds": time.time() - started, "device": str(device),
    }
    (out_dir / "train_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    from plots import plot_history

    plot_history(history_path, out_dir / "training_curves.png")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
