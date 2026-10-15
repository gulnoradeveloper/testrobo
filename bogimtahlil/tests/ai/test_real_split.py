"""Haqiqiy dataset taqsimotini tekshirish (data/splits/manifest_split.csv mavjud bo‘lganda ishlaydi)."""
from pathlib import Path

import pandas as pd
import pytest

SPLIT = Path(__file__).resolve().parents[2] / "data" / "splits" / "manifest_split.csv"
pytestmark = pytest.mark.skipif(not SPLIT.is_file(), reason="real dataset hali tayyorlanmagan (data/splits yo‘q)")


@pytest.fixture(scope="module")
def df():
    return pd.read_csv(SPLIT, dtype={"patient_id": str})


def test_no_patient_in_two_splits(df):
    groups = {s: set(df.loc[df["split"] == s, "patient_id"]) for s in ("train", "val", "test")}
    assert not groups["train"] & groups["val"]
    assert not groups["train"] & groups["test"]
    assert not groups["val"] & groups["test"]


def test_ratios_and_all_classes(df):
    frac = df.groupby("split")["patient_id"].nunique() / df["patient_id"].nunique()
    assert abs(frac["train"] - 0.70) < 0.02 and abs(frac["val"] - 0.15) < 0.02 and abs(frac["test"] - 0.15) < 0.02
    for s in ("train", "val", "test"):
        assert set(df.loc[df["split"] == s, "kl_grade"].astype(int)) == {0, 1, 2, 3, 4}


def test_required_columns(df):
    assert {"image_path", "patient_id", "knee_side", "visit_id", "projection", "kl_grade", "dataset_source", "split"} <= set(df.columns)
