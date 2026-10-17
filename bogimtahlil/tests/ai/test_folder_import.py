"""Chen (Mendeley) dataset tuzilmasini import qilish: faqat kneeKL224 va train/val/test; bemor ID tekshirilmagan deb belgilanadi."""
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]


def test_import_chen_layout(tmp_path):
    for res in ("kneeKL224", "kneeKL299"):
        for split in ("train", "val", "test", "auto_test"):
            for g in range(5):
                d = tmp_path / "KneeXrayData" / "ClsKLData" / res / split / str(g)
                d.mkdir(parents=True)
                Image.fromarray(np.full((8, 8), g * 40, np.uint8)).save(d / f"{split}_{g}.png")
    out = tmp_path / "m.csv"
    r = subprocess.run([sys.executable, str(ROOT / "ai/scripts/import_folder_dataset.py"), "--root", str(tmp_path),
                        "--keep-split", "--path-contains", "kneeKL224", "--source", "test", "--out", str(out)],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    df = pd.read_csv(out)
    assert len(df) == 15  # 3 split × 5 daraja; auto_test va kneeKL299 chiqarilgan
    assert set(df["split"]) == {"train", "val", "test"}
    assert not df["image_path"].str.contains("kneeKL299|auto_test").any()
    assert (df["patient_id_verified"] == False).all()  # noqa: E712
    assert sorted(df[df["split"] == "test"]["kl_grade"]) == [0, 1, 2, 3, 4]


def test_colab_pipeline_selects_224_variant(tmp_path):
    import zipfile

    sys.path.insert(0, str(ROOT / "ai" / "colab"))
    from colab_pipeline import extract_kl

    z = tmp_path / "d.zip"
    with zipfile.ZipFile(z, "w") as f:
        for res in ("kneeKL224", "kneeKL299"):
            for split in ("train", "test", "auto_test"):
                f.writestr(f"K/{res}/{split}/2/a.png", b"x")
        f.writestr("K/Detection/readme.txt", "x")
    root = extract_kl(z, tmp_path / "out")
    assert root.name == "kneeKL224"
    assert sorted(p.parent.parent.name for p in root.rglob("*.png")) == ["test", "train"]
