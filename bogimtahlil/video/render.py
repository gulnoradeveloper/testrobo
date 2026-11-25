"""Bo‘g‘imTahlil taqdimot videosini kod orqali yaratish (~2 daqiqa, 1920×1080, 30 fps).

    python video/capture.py                    # dasturning haqiqiy skrinshotlari (bir marta)
    python video/render.py --preview 3 40 60   # tanlangan soniyalardagi kadrlar (PNG)
    python video/render.py                     # to‘liq video -> video/out/bogimtahlil_taqdimot.mp4

Kadrlar scenes.html dagi render(t) orqali deterministik chiziladi. Fon musiqasi numpy bilan sintez qilinadi
(original kompozitsiya, tashqi namunasiz — mualliflik huquqi muammosi yo‘q).
"""
import argparse
import os
import shutil
import subprocess
import wave
from pathlib import Path

import numpy as np
from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
FPS = 30
W, H = 1920, 1080
CHROME = os.environ.get("BT_CHROME", "/opt/pw-browsers/chromium-1243/chrome-linux64/chrome")
SR = 44100


def ffmpeg_bin():
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    import imageio_ffmpeg

    return imageio_ffmpeg.get_ffmpeg_exe()


def open_page(p):
    kwargs = {"executable_path": CHROME} if Path(CHROME).exists() else {}
    browser = p.chromium.launch(**kwargs)
    page = browser.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
    page.goto((HERE / "scenes.html").as_uri())
    page.wait_for_load_state("networkidle")
    page.evaluate("document.fonts.ready")
    page.evaluate("Promise.all([...document.images].map(i => i.decode().catch(() => null)))")
    return browser, page


def synth_music(duration, path):
    """Sokin, texnologik fon: pad akkordlar (Am–F–C–G), yumshoq arpedjio, bas. 80 BPM."""
    n = int(duration * SR)
    out = np.zeros((n, 2))
    beat, bar = 60 / 80, 4 * 60 / 80
    hz = lambda m: 440.0 * 2 ** ((m - 69) / 12)
    chords = [[57, 60, 64, 69], [53, 57, 60, 65], [48, 52, 55, 64], [55, 59, 62, 67]]
    bass = [45, 41, 36, 43]

    def add(sig, start, pan=0.0):
        i = int(start * SR)
        if i >= n:
            return
        sig = sig[: n - i]
        out[i:i + len(sig), 0] += sig * (1 - pan)
        out[i:i + len(sig), 1] += sig * (1 + pan)

    k, start = 0, 0.0
    while start < duration:
        ch, b = chords[k % 4], bass[k % 4]
        t = np.arange(int(bar * SR)) / SR
        env = np.minimum(1, t / 0.8) * np.minimum(1, (bar - t) / 0.9 + 0.2)
        pad = sum(np.sin(2 * np.pi * hz(m) * t) * .55 + np.sin(2 * np.pi * hz(m) * 1.004 * t) * .4
                  + np.sin(2 * np.pi * hz(m + 12) * t) * .1 for m in ch)
        add(pad * env * 0.03, start)
        bt = np.arange(int(beat * 2 * SR)) / SR
        for off in (0, beat * 2):
            add(np.sin(2 * np.pi * hz(b) * bt) * np.exp(-bt * 2.0) * 0.14, start + off)
        if 6 < start < duration - 7:
            seq = [ch[0] + 12, ch[2] + 12, ch[1] + 12, ch[3] + 12, ch[2] + 12, ch[1] + 24, ch[3] + 12, ch[2] + 12]
            for j, m in enumerate(seq):
                at = np.arange(int(beat * 0.8 * SR)) / SR
                pl = (np.sin(2 * np.pi * hz(m) * at) + .25 * np.sin(2 * np.pi * hz(m) * 3 * at)) * np.exp(-at * 4.5)
                add(pl * 0.035, start + j * beat / 2, pan=.3 if j % 2 else -.3)
        start += bar
        k += 1
    rev = out.copy()
    for d, g in [(0.071, .3), (0.123, .24), (0.197, .18), (0.281, .12), (0.389, .08)]:
        s = int(d * SR)
        rev[s:] += out[:-s] * g
    t_all = np.arange(n) / SR
    rev *= (np.minimum(1, t_all / 2.5) * np.clip((duration - t_all) / 4.0, 0, 1))[:, None]
    rev /= max(1e-9, np.abs(rev).max()) / 0.75
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((rev * 32767).astype("<i2").tobytes())


def render_full():
    OUT.mkdir(exist_ok=True)
    silent, music, final = OUT / "video_silent.mp4", OUT / "music.wav", OUT / "bogimtahlil_taqdimot.mp4"
    ff = ffmpeg_bin()
    with sync_playwright() as p:
        browser, page = open_page(p)
        duration = page.evaluate("window.DURATION")
        total = int(duration * FPS)
        proc = subprocess.Popen(
            [ff, "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(FPS), "-c:v", "mjpeg", "-i", "-",
             "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(silent)],
            stdin=subprocess.PIPE)
        for i in range(total):
            page.evaluate(f"render({i / FPS})")
            proc.stdin.write(page.screenshot(type="jpeg", quality=93))
            if i % (FPS * 10) == 0:
                print(f"kadr {i}/{total}", flush=True)
        proc.stdin.close()
        proc.wait()
        browser.close()
    synth_music(duration, music)
    subprocess.run([ff, "-y", "-loglevel", "error", "-i", str(silent), "-i", str(music), "-c:v", "copy", "-c:a", "aac",
                    "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(final)], check=True)
    silent.unlink()
    web = OUT / "bogimtahlil_taqdimot_web.mp4"  # messenjer/pochta uchun yengil versiya
    common = ["-c:v", "libx264", "-preset", "slow", "-b:v", "1500k", "-maxrate", "2000k", "-bufsize", "4000k", "-pix_fmt", "yuv420p"]
    subprocess.run([ff, "-y", "-loglevel", "error", "-i", str(final), *common, "-pass", "1", "-passlogfile", str(OUT / "pass"),
                    "-an", "-f", "null", "-"], check=True)
    subprocess.run([ff, "-y", "-loglevel", "error", "-i", str(final), *common, "-pass", "2", "-passlogfile", str(OUT / "pass"),
                    "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(web)], check=True)
    for f in OUT.glob("pass*"):
        f.unlink()
    print("Tayyor:", final, "|", web)


def render_preview(times):
    OUT.mkdir(exist_ok=True)
    with sync_playwright() as p:
        browser, page = open_page(p)
        for t in times:
            page.evaluate(f"render({t})")
            page.screenshot(path=str(OUT / f"preview_{t:05.1f}.png"))
        browser.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", nargs="*", type=float)
    args = ap.parse_args()
    render_preview(args.preview) if args.preview else render_full()
