"""Videoda ishlatiladigan platforma skrinshotlarini olish.

Ishga tushirish: `python manage.py runserver 127.0.0.1:8765` (seed_demo bilan) va
    python video/capture.py
"""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

B = "http://127.0.0.1:8765"
OUT = Path(__file__).parent / "assets" / "shots"
PASS = "Begoyim2026!"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"

# (fayl, telefon yoki None, yo'l, scroll qilinadigan selektor)
DESKTOP = [
    ("home", None, "/", None),
    ("register", None, "/royxatdan-otish/", None),
    ("profile", "+998935554433", "/profil/", None),
    ("verify", "+998900000002", "/mahalla/arizalar/9/", None),
    ("service_new", "+998935554433", "/xizmatlar/yangi/", None),
    ("ai", None, "/ai-tavsiya/?text=Ertaga+Buxoro+shahrida+2+ta+xonani+tozalaydigan+ayol+kerak.", ".parsed-chips"),
    ("order", "+998902000001", "/buyurtmalar/5/", None),
    ("income", "+998901000001", "/daromad/", None),
    ("mahalla", "+998900000002", "/mahalla/", None),
    ("psy", None, "/psixologik-yordam/", None),
    ("list", None, "/xizmatlar/", None),
]
FULL_PAGE = {"m_service"}
MOBILE = [("m_home", None, "/", None), ("m_cats", None, "/", "#categories"), ("m_service", "+998902000001", "/xizmatlar/1/", None)]


def shoot(browser, items, viewport, scale):
    for name, phone, path, sel in items:
        ctx = browser.new_context(viewport=viewport, device_scale_factor=scale)
        pg = ctx.new_page()
        if phone:
            pg.goto(B + "/kirish/")
            pg.fill("#id_phone", phone)
            pg.fill("#id_password", PASS)
            pg.click("form button[type=submit]")
        pg.goto(B + path)
        pg.wait_for_load_state("networkidle")
        if sel:
            pg.locator(sel).first.scroll_into_view_if_needed()
            pg.evaluate("window.scrollBy(0, -140)")
        pg.wait_for_timeout(500)
        pg.screenshot(path=str(OUT / f"{name}.png"), full_page=name in FULL_PAGE)
        ctx.close()
        print("ok", name)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        br = p.chromium.launch(executable_path=CHROME if len(sys.argv) < 2 else sys.argv[1])
        shoot(br, DESKTOP, {"width": 1440, "height": 900}, 1.5)
        shoot(br, MOBILE, {"width": 390, "height": 844}, 3)
        br.close()
