import numpy as np
import pandas as pd

from kltool.data import check_patient_leakage, class_weights, patient_split, validate_manifest
from kltool.metrics import compute_metrics


def test_perfect_prediction_metrics():
    y = [0, 1, 2, 3, 4, 0, 1, 2]
    m = compute_metrics(y, y)
    assert m["accuracy"] == 1.0 and m["macro_f1"] == 1.0 and m["quadratic_weighted_kappa"] == 1.0
    assert m["balanced_accuracy"] == 1.0
    assert np.trace(np.array(m["confusion_matrix"])) == len(y)


def test_metrics_values_and_early_confusion():
    y_true = [0, 0, 1, 1, 2, 2, 3, 4]
    y_pred = [0, 1, 0, 1, 1, 2, 3, 4]
    m = compute_metrics(y_true, y_pred)
    assert m["accuracy"] == 5 / 8
    assert m["per_class"]["KL1"]["recall"] == 0.5
    ec = m["early_grade_confusion"]
    assert ec["pairs"]["KL0->KL1"]["count"] == 1
    assert ec["pairs"]["KL1->KL0"]["count"] == 1
    assert ec["pairs"]["KL2->KL1"]["count"] == 1
    assert ec["errors_within_kl0_kl2"] == 3
    # QWK: yaqin darajalardagi xato uzoq xatodan kamroq jazolanadi
    far = compute_metrics(y_true, [4, 0, 1, 1, 2, 2, 3, 4])
    assert far["quadratic_weighted_kappa"] < m["quadratic_weighted_kappa"] + 1e-9


def _manifest(n_patients=200, seed=0):
    rng = np.random.default_rng(seed)
    rows = []
    for p in range(n_patients):
        for side in ("L", "R"):
            for tp in ("V00", "V01"):
                rows.append({"image_path": f"x/{p}_{side}_{tp}.png", "patient_id": f"P{p:04d}", "knee_side": side,
                             "projection": "PA", "visit_id": tp, "dataset_source": "test", "kl_grade": int(rng.integers(0, 5))})
    return pd.DataFrame(rows)


def test_patient_split_no_leakage_and_ratios():
    df = patient_split(_manifest(), 0.15, 0.15, seed=42)
    assert check_patient_leakage(df) == []
    frac = df.groupby("split")["patient_id"].nunique() / df["patient_id"].nunique()
    assert abs(frac["train"] - 0.70) < 0.03 and abs(frac["val"] - 0.15) < 0.03 and abs(frac["test"] - 0.15) < 0.03


def test_split_reproducible():
    a = patient_split(_manifest(), seed=42)["split"].tolist()
    b = patient_split(_manifest(), seed=42)["split"].tolist()
    assert a == b


def test_validate_manifest_detects_problems():
    df = _manifest(5)
    df.loc[0, "kl_grade"] = 7
    df.loc[1, "projection"] = "LATERAL"
    df.loc[2, ["patient_id", "knee_side", "visit_id"]] = df.loc[3, ["patient_id", "knee_side", "visit_id"]].values
    rep = validate_manifest(df, check_files=False)
    assert rep["invalid_grades"] == 1 and rep["non_frontal"] == 1 and rep["duplicate_keys"] >= 2


def test_class_weights_inverse_frequency():
    w = class_weights([0] * 80 + [1] * 10 + [2] * 5 + [3] * 3 + [4] * 2)
    assert w.argmin() == 0 and w.argmax() == 4
    assert abs(w.mean() - 1) < 1e-6


def test_split_summary_counts_classes_per_split():
    from kltool.data import split_summary

    df = patient_split(_manifest(), seed=42)
    s = split_summary(df)
    assert sum(v["images"] for v in s.values()) == len(df)
    for split, v in s.items():
        assert sum(v["classes"].values()) == v["images"]
        assert v["classes"]["KL3"] == int(((df["split"] == split) & (df["kl_grade"] == 3)).sum())


def test_legacy_column_names_are_mapped(tmp_path):
    from kltool.data import load_manifest

    p = tmp_path / "m.csv"
    p.write_text("image_path,patient_id,side,view,timepoint,kl_grade\nx.png,P1,l,pa,V00,2\n")
    df = load_manifest(p)
    assert df.loc[0, "knee_side"] == "L" and df.loc[0, "projection"] == "PA" and df.loc[0, "visit_id"] == "V00"
