"""OAI moslashtirish modulining testlari (sintetik, OAI formatidagi kichik fayllar bilan)."""
import pandas as pd
import pytest
from pathlib import Path

from kltool.oai import (OAIFormatError, link_images_to_labels, load_config, parse_code, read_image_index,
                        read_kl_labels, resolve_duplicate_reads, visit_from_filename)

CFG = load_config(Path(__file__).resolve().parents[2] / "ai" / "configs" / "oai_columns.yaml")


@pytest.mark.parametrize("raw,expected", [
    ("2", 2), ("2: 2", 2), ("1: Right", 1), (" 0 ", 0), (".: Missing Form/Incomplete Workbook", None),
    (".A: Not Expected", None), ("", None), (None, None), (3.0, 3), ("abc", None),
])
def test_parse_code(raw, expected):
    assert parse_code(raw) == expected


def test_config_is_marked_unverified():
    # Ustun nomlari hujjat bilan solishtirilmaguncha konfiguratsiya "verified: false" bo‘lishi shart
    assert CFG["verified"] is False


def _write(tmp_path, name, text):
    p = tmp_path / name
    p.write_text(text)
    return p


def test_read_labels_maps_side_visit_and_drops_missing(tmp_path):
    p = _write(tmp_path, "kXR_SQ_BU01.txt",
               "ID|SIDE|READPRJ|V01XRKL\n9000001|1: Right|15|3\n9000001|2: Left|15|.: Missing\n9000002|2|15|7\n9000003|9|15|1\n")
    df, st = read_kl_labels(p, CFG)
    assert visit_from_filename(p, CFG["visits"]) == "V01"
    assert df.to_dict("records")[0] == {"patient_id": "9000001", "knee_side": "R", "visit_id": "V01", "kl_grade": 3,
                                        "read_project": "15", "label_file": "kXR_SQ_BU01.txt"}
    assert len(df) == 1 and st["missing_kl"] == 1 and st["invalid_kl"] == 1 and st["unknown_side"] == 1


def test_missing_column_fails_loudly(tmp_path):
    p = _write(tmp_path, "kXR_SQ_BU00.txt", "ID|SIDE|V00XRJSM\n1|1|0\n")
    with pytest.raises(OAIFormatError, match="V00XRKL"):
        read_kl_labels(p, CFG)


def test_unknown_visit_fails(tmp_path):
    with pytest.raises(OAIFormatError):
        visit_from_filename(tmp_path / "kXR_SQ_BU99.txt", CFG["visits"])


def test_duplicate_reads_policy():
    labels = pd.DataFrame([
        {"patient_id": "1", "knee_side": "R", "visit_id": "V00", "kl_grade": 2, "read_project": "15"},
        {"patient_id": "1", "knee_side": "R", "visit_id": "V00", "kl_grade": 2, "read_project": "37"},  # mos
        {"patient_id": "2", "knee_side": "L", "visit_id": "V00", "kl_grade": 1, "read_project": "15"},
        {"patient_id": "2", "knee_side": "L", "visit_id": "V00", "kl_grade": 3, "read_project": "37"},  # ziddiyat
    ])
    kept, st = resolve_duplicate_reads(labels)
    assert kept["patient_id"].tolist() == ["1"] and st["keys_with_conflicting_reads"] == 1
    kept2, _ = resolve_duplicate_reads(labels, "prefer_project", ["37", "15"])
    assert dict(zip(kept2["patient_id"], kept2["kl_grade"])) == {"1": 2, "2": 3}


def test_link_one_to_one(tmp_path):
    idx = _write(tmp_path, "index.csv", "image_path,patient_id,knee_side,visit_id,projection\n"
                 "a.png,1,R,V00,PA\nb.png,1,L,V00,pa\nc.png,2,R,V00,LATERAL\nd.png,3,R,V00,PA\nd2.png,3,R,V00,PA\n"
                 "e.png,4,R,V01,PA\n")
    labels = pd.DataFrame([
        {"patient_id": "1", "knee_side": "R", "visit_id": "V00", "kl_grade": 2, "read_project": "15", "label_file": "f"},
        {"patient_id": "1", "knee_side": "L", "visit_id": "V00", "kl_grade": 0, "read_project": "15", "label_file": "f"},
        {"patient_id": "3", "knee_side": "R", "visit_id": "V00", "kl_grade": 4, "read_project": "15", "label_file": "f"},
    ])
    m, st = link_images_to_labels(read_image_index(idx, CFG), labels)
    assert sorted(Path(p).name for p in m["image_path"]) == ["a.png", "b.png"]
    # Tomon almashib ketmagan: chap tizza tasviri chap tizza yorlig‘i bilan
    assert dict(zip(m["knee_side"], m["kl_grade"])) == {"R": 2, "L": 0}
    assert st == {"images_in_index": 6, "images_bad_side": 0, "images_non_frontal": 1, "images_with_duplicate_key": 2,
                  "images_without_label": 1, "linked": 2, "labels_without_image": 1}
    assert set(m.columns) >= {"image_path", "patient_id", "knee_side", "visit_id", "projection", "kl_grade", "dataset_source"}
    assert (m["dataset_source"] == "OAI").all()
