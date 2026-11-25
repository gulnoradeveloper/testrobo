"""Video uchun dasturning haqiqiy skrinshotlari (o‘qitilgan model bilan).

    python video/capture.py     # bogimtahlil/ ildizidan; server avtomatik ishga tushiriladi

Natija: video/assets/shot_*.png, video/assets/pdf_page1.png, video/assets/kl/*.png
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
ASSETS = HERE / "assets"
PORT = 8799
URL = f"http://127.0.0.1:{PORT}"
CHROME = os.environ.get("BT_CHROME", "/opt/pw-browsers/chromium-1243/chrome-linux64/chrome")


def wait_ready(timeout=300):
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            with urllib.request.urlopen(URL + "/api/v1/health", timeout=2) as r:
                if r.status == 200:
                    return
        except Exception:
            time.sleep(1)
    raise SystemExit("server ishga tushmadi")


def main() -> None:
    ASSETS.mkdir(exist_ok=True)
    tmp = Path(tempfile.mkdtemp())
    env = {**os.environ, "BT_DATABASE_URL": f"sqlite:///{(tmp / 'db.sqlite').as_posix()}",
           "BT_STORAGE_DIR": str(tmp / "st")}
    srv = subprocess.Popen([sys.executable, "-m", "uvicorn", "app.main:app", "--port", str(PORT)], cwd=ROOT / "backend",
                           env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        wait_ready()
        with sync_playwright() as p:
            kw = {"executable_path": CHROME} if Path(CHROME).exists() else {}
            b = p.chromium.launch(**kw)
            ctx = b.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=1.5, accept_downloads=True)
            pg = ctx.new_page()

            def shot(name, full=True, wait=1200):
                pg.wait_for_timeout(wait)
                pg.screenshot(path=str(ASSETS / f"shot_{name}.png"), full_page=full)

            pg.goto(URL + "/")
            pg.wait_for_selector("text=Model yuklangan")
            shot("home")

            # Bir nechta tahlil (tarix uchun), oxirgisi — KL4 namunasi
            for img in ("KL2_2.png", "KL0_2.png", "KL4_1.png"):
                pg.goto(URL + "/tahlil")
                pg.set_input_files('input[type="file"]', str(ROOT / "demo_images" / img))
                pg.get_by_role("checkbox").click()
                if img == "KL4_1.png":
                    pg.evaluate("window.scrollTo(0, 0)")
                    shot("upload")
                pg.get_by_role("button", name="Sun’iy intellekt yordamida tahlil qilish").click()
                pg.wait_for_url("**/natija/**", timeout=60000)
                pg.wait_for_selector("text=Bashorat qilingan daraja:")
            shot("result", wait=2000)
            with pg.expect_download() as dl:
                pg.get_by_role("link", name="PDF hisobotni yuklab olish").click()
            pdf = tmp / "report.pdf"
            dl.value.save_as(str(pdf))

            pg.goto(URL + "/tarix")
            pg.wait_for_selector("text=Jami:")
            shot("history", full=False)
            pg.goto(URL + "/model")
            pg.wait_for_selector("text=Model pasporti")
            shot("model", wait=2500)
            b.close()
        subprocess.run(["pdftoppm", "-r", "110", "-png", "-f", "1", "-l", "1", "-singlefile", str(pdf),
                        str(ASSETS / "pdf_page1")], check=True)
        kl = ASSETS / "kl"
        kl.mkdir(exist_ok=True)
        for g in range(5):
            shutil.copy(ROOT / "demo_images" / f"KL{g}_1.png", kl / f"KL{g}.png")
        print("Skrinshotlar:", sorted(x.name for x in ASSETS.glob("*.png")))
    finally:
        srv.terminate()
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
