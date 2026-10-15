"""Baholash metrikalari: accuracy, balanced accuracy, precision/recall/F1, QWK, confusion matrix."""
from __future__ import annotations

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    cohen_kappa_score,
    confusion_matrix,
    precision_recall_fscore_support,
)

from . import KL_CLASSES


def compute_metrics(y_true, y_pred, class_names=KL_CLASSES) -> dict:
    y_true = np.asarray(y_true, dtype=int)
    y_pred = np.asarray(y_pred, dtype=int)
    labels = list(range(len(class_names)))
    prec, rec, f1, support = precision_recall_fscore_support(y_true, y_pred, labels=labels, zero_division=0)
    macro_p, macro_r, macro_f1, _ = precision_recall_fscore_support(
        y_true, y_pred, labels=labels, average="macro", zero_division=0
    )
    cm = confusion_matrix(y_true, y_pred, labels=labels)
    return {
        "n_samples": int(len(y_true)),
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "macro_precision": float(macro_p),
        "macro_recall": float(macro_r),
        "macro_f1": float(macro_f1),
        "quadratic_weighted_kappa": float(cohen_kappa_score(y_true, y_pred, labels=labels, weights="quadratic")),
        "per_class": {
            name: {
                "precision": float(prec[i]),
                "recall": float(rec[i]),
                "f1": float(f1[i]),
                "support": int(support[i]),
            }
            for i, name in enumerate(class_names)
        },
        "confusion_matrix": cm.tolist(),
        "early_grade_confusion": early_grade_confusion(cm, class_names),
    }


def early_grade_confusion(cm, class_names=KL_CLASSES) -> dict:
    """KL0, KL1, KL2 sinflarining o‘zaro chalkashishi (TT 5.5-band)."""
    cm = np.asarray(cm)
    sub = cm[:3, :3]
    rows = sub.sum(axis=1)
    pairs = {}
    for i in range(3):
        for j in range(3):
            if i == j:
                continue
            rate = float(sub[i, j] / cm[i].sum()) if cm[i].sum() else 0.0
            pairs[f"{class_names[i]}->{class_names[j]}"] = {"count": int(sub[i, j]), "rate_of_true_class": rate}
    within = int(sub.sum() - np.trace(sub))
    total_early = int(cm[:3].sum())
    return {
        "submatrix": sub.tolist(),
        "pairs": pairs,
        "errors_within_kl0_kl2": within,
        "samples_kl0_kl2": total_early,
        "error_rate_within_kl0_kl2": float(within / total_early) if total_early else 0.0,
        "row_totals": rows.tolist(),
    }
