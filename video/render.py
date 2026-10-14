"""BEGOYIM taqdimot videosini kod orqali yaratish.

    python video/render.py --preview 3 10 30   # tanlangan soniyalardagi kadrlar (PNG)
    python video/render.py                     # to'liq video -> video/out/begoyim_taqdimot.mp4

Talablar: playwright (Chromium), numpy, ffmpeg (PATH yoki imageio-ffmpeg).
Kadrlar scenes.html dagi render(t) funksiyasi orqali deterministik chiziladi,
fon musiqasi numpy bilan sintez qilinadi (mualliflik huquqi muammosi yo'q).
"""
import argparse
import shutil
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np
from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
FPS = 30
W, H = 1920, 1080
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"


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


# ---------------- Musiqa ----------------
SR = 44100


def note(freq, dur, sr=SR):
    t = np.arange(int(dur * sr)) / sr
    return t, freq


def synth_music(duration, path):
    """Yumshoq, iliq fon: pad akkordlar + arpedjio + engil bas. Tempo 84 BPM."""
    n = int(duration * SR)
    out = np.zeros((n, 2))
    beat = 60 / 84
    bar = beat * 4
    # F - C - Dm - Bb (iliq, umidli progressiya)
    A4 = 440.0
    hz = lambda m: A4 * 2 ** ((m - 69) / 12)
    chords = [[53, 57, 60, 65], [48, 52, 55, 64], [50, 53, 57, 62], [46, 50, 53, 62]]
    bass = [41, 36, 38, 34]
    t_all = np.arange(n) / SR

    def add(sig, start, pan=0.0):
        i = int(start * SR)
        if i >= n:
            return
        sig = sig[: n - i]
        out[i:i + len(sig), 0] += sig * (1 - pan) * 0.5 * 2
        out[i:i + len(sig), 1] += sig * (1 + pan) * 0.5 * 2

    k = 0
    start = 0.0
    while start < duration:
        ch, b = chords[k % 4], bass[k % 4]
        L = bar
        t = np.arange(int(L * SR)) / SR
        env = np.minimum(1, t / 0.6) * np.minimum(1, (L - t) / 0.8 + 0.15)
        pad = sum(
            np.sin(2 * np.pi * hz(m) * t) * 0.6 + np.sin(2 * np.pi * hz(m) * 1.003 * t) * 0.4 + np.sin(2 * np.pi * hz(m + 12) * t) * 0.12
            for m in ch
        )
        add(pad * env * 0.035, start)
        bt = np.arange(int(beat * 2 * SR)) / SR
        add(np.sin(2 * np.pi * hz(b) * bt) * np.exp(-bt * 2.2) * 0.16, start)
        add(np.sin(2 * np.pi * hz(b) * bt) * np.exp(-bt * 2.2) * 0.11, start + beat * 2)
        # Arpedjio (intro va finaldan tashqari yoqiladi)
        if 4 < start < duration - 6:
            seq = [ch[0] + 12, ch[1] + 12, ch[2] + 12, ch[3] + 12, ch[2] + 12, ch[1] + 12, ch[3] + 12, ch[2] + 24]
            for j, m in enumerate(seq):
                at = np.arange(int(beat * 0.9 * SR)) / SR
                pl = (np.sin(2 * np.pi * hz(m) * at) + 0.3 * np.sin(2 * np.pi * hz(m) * 2 * at)) * np.exp(-at * 5)
                add(pl * 0.045, start + j * beat / 2, pan=0.35 if j % 2 else -0.35)
        start += L
        k += 1
    # Oddiy reverb (kechikishlar yig'indisi)
    rev = out.copy()
    for d, g in [(0.083, .28), (0.137, .22), (0.211, .16), (0.293, .11)]:
        s = int(d * SR)
        rev[s:] += out[:-s] * g
    out = rev
    fade_in = np.minimum(1, t_all / 2.0)
    fade_out = np.clip((duration - t_all) / 3.5, 0, 1)
    out *= (fade_in * fade_out)[:, None]
    out /= max(1e-9, np.abs(out).max()) / 0.8
    pcm = (out * 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def prepare_music(src, duration, path):
    """Tayyor trekni video uzunligiga moslash: kesish, fade in/out, ovoz balandligini normallash."""
    subprocess.run(
        [ffmpeg_bin(), "-y", "-loglevel", "error", "-i", str(src), "-t", str(duration),
         "-af", f"afade=t=in:d=1.5,afade=t=out:st={duration - 4.5}:d=4.5,loudnorm=I=-16:TP=-1.5:LRA=11",
         "-ar", "44100", "-ac", "2", str(path)],
        check=True,
    )


def render_full(music_src=None):
    OUT.mkdir(exist_ok=True)
    silent = OUT / "video_silent.mp4"
    music = OUT / "music.wav"
    final = OUT / "begoyim_taqdimot.mp4"
    ff = ffmpeg_bin()
    with sync_playwright() as p:
        browser, page = open_page(p)
        duration = page.evaluate("window.DURATION")
        total = int(duration * FPS)
        proc = subprocess.Popen(
            [ff, "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(FPS), "-c:v", "mjpeg", "-i", "-",
             "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(silent)],
            stdin=subprocess.PIPE,
        )
        for i in range(total):
            page.evaluate(f"render({i / FPS})")
            proc.stdin.write(page.screenshot(type="jpeg", quality=93))
            if i % (FPS * 5) == 0:
                print(f"kadr {i}/{total}", flush=True)
        proc.stdin.close()
        proc.wait()
        browser.close()
    if music_src:
        prepare_music(music_src, duration, music)
    else:
        from music import compose, write_wav  # original kompozitsiya (music.py)

        write_wav(compose(duration), music)
    subprocess.run(
        [ff, "-y", "-loglevel", "error", "-i", str(silent), "-i", str(music), "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
         "-shortest", "-movflags", "+faststart", str(final)],
        check=True,
    )
    silent.unlink()
    # Messenjer/pochta uchun yengil versiya (~1.3 Mbit/s, 30 MB dan kichik, ikki o'tishli)
    web = OUT / "begoyim_taqdimot_web.mp4"
    common = ["-c:v", "libx264", "-preset", "slow", "-b:v", "1300k", "-maxrate", "1800k", "-bufsize", "4000k", "-pix_fmt", "yuv420p"]
    subprocess.run([ff, "-y", "-loglevel", "error", "-i", str(final), *common, "-pass", "1", "-passlogfile", str(OUT / "pass"), "-an", "-f", "null", "-"], check=True)
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
    ap.add_argument("--music", help="tayyor fon musiqasi (masalan, separate.py bilan olingan minus)")
    args = ap.parse_args()
    if args.preview:
        render_preview(args.preview)
    else:
        render_full(args.music)
    sys.exit(0)
