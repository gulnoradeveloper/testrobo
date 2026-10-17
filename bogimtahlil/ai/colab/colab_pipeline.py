"""Google Colab’da (bepul GPU) modelni o‘qitish — butun jarayon bitta buyruqda.

    python ai/colab/colab_pipeline.py --data "<KneeXrayData.zip havolasi yoki yo‘li>"

Dataset: Chen P. "Knee Osteoarthritis Severity Grading Dataset", Mendeley Data, v1, 2018,
doi:10.17632/56rmx5bjcr.1 (OAI asosida tayyorlangan, tizzalar alohida kesilgan, KL0–KL4 papkalarda).

Bosqichlar:
 1. Datasetni yuklab olish (Colab serveriga, sizning kompyuteringizga emas).
 2. Arxivdan faqat KL tasniflash qismini ajratish (train/val/test/<0..4>/*.png; 224 piksel varianti afzal).
 3. Manifest: ai/scripts/import_folder_dataset.py (datasetning tayyor train/val/test taqsimoti saqlanadi).
 4. ai/scripts/run_experiment.py — ResNet-18 va EfficientNet-B0, validation bo‘yicha tanlash, test, eksport.
 5. Test guruhidan 10 ta haqiqiy rentgen tasviri (har bir KL darajadan 2 tadan) — dasturni sinash uchun.
 6. Natijalarni bitta ZIP ga yig‘ish: artifacts/model.pt, experiments/, data/splits/dataset_report.json, demo_images/.
"""
from __future__ import annotations

import argparse
import random
import re
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "ai" / "scripts"
DATASET_NAME = "Knee Osteoarthritis Severity Grading Dataset (Chen, Mendeley Data 2018; OAI asosida)"
DATASET_LICENSE = "CC BY 4.0 (Mendeley Data sahifasida tekshiring); manba: Osteoarthritis Initiative"
MEMBER_RE = re.compile(r"^(?P<prefix>(?:.*/)?)(?P<split>train|val|test)/(?P<grade>[0-4])/[^/]+\.(png|jpe?g)$", re.I)


def run(*args) -> None:
    print("\n$", " ".join(str(a) for a in args), flush=True)
    r = subprocess.run([sys.executable, *map(str, args)], cwd=ROOT)
    if r.returncode:
        raise SystemExit(f"Bosqich xato bilan tugadi: {args[0]}")


def download(src: str, dest: Path) -> Path:
    if not src.startswith(("http://", "https://")):
        p = Path(src).expanduser()
        if not p.exists():
            raise SystemExit(f"Topilmadi: {p}")
        return p
    if dest.is_file() and dest.stat().st_size > 0:
        print(f"Arxiv allaqachon yuklangan: {dest}")
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"Yuklab olinmoqda: {src}")
    req = urllib.request.Request(src, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as r, open(dest, "wb") as f:
        total, done, last = int(r.headers.get("Content-Length") or 0), 0, -1
        while chunk := r.read(8 << 20):
            f.write(chunk)
            done += len(chunk)
            pct = int(done * 100 / total) if total else -1
            if pct != last and pct % 5 == 0:
                print(f"  {done / 2**30:.2f} GB" + (f" ({pct}%)" if total else ""), flush=True)
                last = pct
    if not zipfile.is_zipfile(dest):
        dest.unlink()
        raise SystemExit("Yuklangan fayl ZIP emas — havolani tekshiring (Mendeley sahifasidagi KneeXrayData.zip "
                         "yuklash tugmasi havolasini nusxalang).")
    return dest


def extract_kl(zip_path: Path, out: Path) -> Path:
    """Arxivdan train/val/test/<0..4> tuzilmasidagi KL tasniflash tasvirlarini ajratadi."""
    with zipfile.ZipFile(zip_path) as z:
        groups: dict[str, list[str]] = {}
        for name in z.namelist():
            m = MEMBER_RE.match(name.replace("\\", "/"))
            if m:
                groups.setdefault(m.group("prefix"), []).append(name)
        if not groups:
            raise SystemExit("Arxivda train/val/test/<0..4>/ tuzilmasidagi tasvirlar topilmadi")
        # 224 piksel varianti bo‘lsa — o‘sha (model kirishi 224×224); aks holda eng katta guruh
        prefix = sorted(groups, key=lambda p: ("224" not in p, -len(groups[p])))[0]
        print(f"Tanlangan qism: '{prefix or '/'}' — {len(groups[prefix])} ta tasvir")
        for name in groups[prefix]:
            z.extract(name, out)
    return out / prefix




def pick_demo_images(manifest: Path, dest: Path, per_class: int = 2, seed: int = 42) -> list[Path]:
    import pandas as pd

    df = pd.read_csv(manifest, dtype=str)
    df = df[df["split"] == "test"]
    rng = random.Random(seed)
    dest.mkdir(parents=True, exist_ok=True)
    out = []
    for g in range(5):
        rows = df[df["kl_grade"].astype(float).astype(int) == g]["image_path"].tolist()
        for i, src in enumerate(rng.sample(rows, min(per_class, len(rows))), 1):
            p = dest / f"KL{g}_{i}{Path(src).suffix.lower()}"
            shutil.copy2(src, p)
            out.append(p)
    (dest / "README.txt").write_text(
        "Dasturni sinash uchun haqiqiy tizza rentgen tasvirlari (test guruhidan, model o‘qitishda ishlatilmagan).\n"
        "Fayl nomidagi KL daraja — datasetdagi mutaxassis bahosi (yorliq), model natijasi bilan solishtirish uchun.\n"
        f"Manba: {DATASET_NAME}. Litsenziya: {DATASET_LICENSE}.\n", encoding="utf-8")
    return out


def package(out_zip: Path, demo: Path) -> None:
    items = [ROOT / "artifacts" / n for n in ("model.pt", "model.pt.sha256", "model_card.json")]
    items.append(ROOT / "data" / "splits" / "dataset_report.json")
    with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as z:
        for p in items:
            if p.is_file():
                z.write(p, p.relative_to(ROOT).as_posix())
        for p in (ROOT / "experiments").rglob("*"):
            if p.is_file() and p.suffix != ".pt":
                z.write(p, p.relative_to(ROOT).as_posix())
        for p in demo.iterdir():
            z.write(p, f"demo_images/{p.name}")
    print(f"\nNatijalar: {out_zip} ({out_zip.stat().st_size / 2**20:.1f} MB)")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data", required=True, help="KneeXrayData.zip havolasi, ZIP fayl yoki ochilgan papka")
    ap.add_argument("--work", default="/content/knee_data" if Path("/content").is_dir() else "knee_data")
    ap.add_argument("--epochs", type=int, default=30)
    ap.add_argument("--num-workers", type=int, default=2)
    ap.add_argument("--out-zip", default="bogimtahlil_model_natijalari.zip")
    ap.add_argument("--no-pretrained", action="store_true", help="faqat lokal smoke-test uchun")
    ap.add_argument("--source-name", default=DATASET_NAME)
    args = ap.parse_args()

    work = Path(args.work).resolve()
    src = download(args.data, work / "KneeXrayData.zip")
    root = extract_kl(src, work / "extracted") if src.is_file() else src

    manifest = ROOT / "data" / "raw" / "manifest.csv"
    run(SCRIPTS / "import_folder_dataset.py", "--root", root, "--keep-split", "--out", manifest,
        "--source", args.source_name)
    exp = [SCRIPTS / "run_experiment.py", "--manifest", manifest, "--keep-existing-split",
           "--dataset-name", args.source_name, "--dataset-license", DATASET_LICENSE,
           "--dataset-notes", "Datasetda bemor ID yo‘q; datasetning o‘z train/val/test taqsimoti ishlatilgan",
           "--epochs", args.epochs, "--num-workers", args.num_workers]
    if args.no_pretrained:
        exp.append("--no-pretrained")
    run(*exp)
    demo = pick_demo_images(ROOT / "data" / "splits" / "manifest_split.csv", ROOT / "demo_images")
    print(f"Sinov tasvirlari: {len(demo)} ta → {ROOT / 'demo_images'}")
    package(Path(args.out_zip).resolve(), ROOT / "demo_images")
    print("\n" + (ROOT / "experiments" / "EXPERIMENT_REPORT.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
