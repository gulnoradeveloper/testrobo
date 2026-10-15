"""Eksperiment grafiklari (Matplotlib)."""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def plot_history(history_csv: str | Path, out_png: str | Path) -> None:
    h = pd.read_csv(history_csv)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    axes[0].plot(h["epoch"], h["train_loss"], label="train loss")
    axes[0].plot(h["epoch"], h["val_loss"], label="validation loss")
    axes[0].set_xlabel("epoch"); axes[0].legend(); axes[0].set_title("Xatolik (loss)")
    axes[1].plot(h["epoch"], h["val_accuracy"], label="val accuracy")
    axes[1].plot(h["epoch"], h["val_macro_f1"], label="val macro F1")
    axes[1].set_xlabel("epoch"); axes[1].legend(); axes[1].set_title("Validation metrikalari")
    fig.tight_layout(); fig.savefig(out_png, dpi=150); plt.close(fig)


def plot_confusion(cm, class_names, out_png: str | Path, title: str = "Confusion matrix") -> None:
    cm = np.asarray(cm)
    norm = cm / np.maximum(cm.sum(axis=1, keepdims=True), 1)
    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(norm, cmap="Blues", vmin=0, vmax=1)
    ax.set_xticks(range(len(class_names)), class_names)
    ax.set_yticks(range(len(class_names)), class_names)
    ax.set_xlabel("Bashorat"); ax.set_ylabel("Haqiqiy (yorliq)"); ax.set_title(title)
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, f"{cm[i, j]}\n{norm[i, j]:.0%}", ha="center", va="center",
                    color="white" if norm[i, j] > 0.5 else "black", fontsize=8)
    fig.colorbar(im, ax=ax, fraction=0.046)
    fig.tight_layout(); fig.savefig(out_png, dpi=150); plt.close(fig)
