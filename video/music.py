"""BEGOYIM videosi uchun original fon musiqasi (kod orqali sintez).

Uslub: iliq, ayollarga xos, o'zbekona ohang — dutorga o'xshash tor (Karplus-Strong),
nayga o'xshash kuy, doira usuli, yumshoq fon akkordlari. Re minor, 96 BPM,
Andalusiya kadensiyasi (Dm–C–Bb–A) va finalda yorug' ko'tarilish (F–C–Dm–Bb).

    python video/music.py out.wav [--duration 150]

Hech qanday tashqi namuna (sample) ishlatilmaydi — mualliflik huquqi muammosi yo'q.
"""
import argparse
import wave

import numpy as np
from scipy.signal import butter, fftconvolve, lfilter, sosfilt

SR = 44100
BPM = 96
BEAT = 60 / BPM
BAR = BEAT * 4
rng = np.random.default_rng(2026)


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


# ---------------- Cholg'ular ----------------

def pluck(m, dur, vel=1.0, bright=0.5):
    """Dutor/rubob: Karplus-Strong."""
    f = hz(m)
    n = int(SR * dur)
    p = max(2, int(round(SR / f)))
    exc = rng.uniform(-1, 1, p) * vel
    exc = lfilter([bright, 1 - bright], [1], exc)  # yumshatilgan zarba
    x = np.zeros(n)
    x[:p] = exc
    d = 0.996
    a = np.zeros(p + 2)
    a[0] = 1
    a[p] = -d / 2
    a[p + 1] = -d / 2
    y = lfilter([1], a, x)
    env = np.minimum(1, np.linspace(0, dur / 0.004, n)) * np.exp(-np.linspace(0, dur, n) * 1.3)
    return y * env


def flute(m, dur, vel=1.0):
    """Nay: sinus + garmonikalar + vibrato + nafas shovqini."""
    n = int(SR * dur)
    t = np.arange(n) / SR
    vib = 1 + 0.006 * np.sin(2 * np.pi * 5.2 * t) * np.minimum(1, t / 0.35)
    ph = 2 * np.pi * hz(m) * np.cumsum(vib) / SR
    tone = np.sin(ph) + 0.28 * np.sin(2 * ph) + 0.08 * np.sin(3 * ph)
    breath = sosfilt(butter(2, [hz(m) * 0.8, hz(m) * 3], "bandpass", fs=SR, output="sos"), rng.normal(0, 1, n)) * 0.08
    att, rel = 0.07, min(0.25, dur * 0.4)
    env = np.minimum(1, t / att) * np.clip((dur - t) / rel, 0, 1)
    return (tone + breath) * env * vel


def pad(ms, dur, vel=1.0):
    """Yumshoq fon akkordi: detyunlangan arra to'lqini + past chastotali filtr."""
    n = int(SR * dur)
    t = np.arange(n) / SR
    sig = np.zeros(n)
    for m in ms:
        for det in (-0.08, 0.0, 0.08):
            f = hz(m + det)
            sig += 2 * ((t * f) % 1) - 1
    sig = sosfilt(butter(2, 1400, "lowpass", fs=SR, output="sos"), sig) / (len(ms) * 3)
    env = np.minimum(1, t / 0.9) * np.clip((dur - t) / 0.9, 0, 1)
    return sig * env * vel


def dum(vel=1.0):
    n = int(SR * 0.45)
    t = np.arange(n) / SR
    f = 62 + 70 * np.exp(-t * 28)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7)
    click = rng.normal(0, 1, n) * np.exp(-t * 180) * 0.25
    return (body + click) * vel


def tak(vel=1.0):
    n = int(SR * 0.16)
    t = np.arange(n) / SR
    noise = sosfilt(butter(2, [1800, 6500], "bandpass", fs=SR, output="sos"), rng.normal(0, 1, n))
    ring = np.sin(2 * np.pi * 420 * t) * 0.3
    return (noise * 1.4 + ring) * np.exp(-t * 38) * vel


def zil(vel=1.0):
    """Doira halqachalari (jingles)."""
    n = int(SR * 0.22)
    t = np.arange(n) / SR
    noise = sosfilt(butter(2, 7000, "highpass", fs=SR, output="sos"), rng.normal(0, 1, n))
    return noise * np.exp(-t * 22) * vel


# ---------------- Kompozitsiya ----------------

CH = {  # akkordlar (MIDI)
    "Dm": [50, 57, 62, 65], "C": [48, 55, 60, 64], "Bb": [46, 53, 58, 62], "A": [45, 52, 57, 61],
    "F": [41, 53, 57, 60], "Gm": [43, 55, 58, 62],
}
ANDALUS = ["Dm", "C", "Bb", "A"]
LIFT = ["F", "C", "Dm", "Bb"]

# Kuylar: (MIDI, davomiyligi zarbalarda); None — pauza
MEL_A = [(69, 1), (74, 1), (77, 1), (76, .5), (74, .5),
         (76, 1.5), (79, .5), (77, 1), (76, 1),
         (74, 1), (77, 1), (82, 1), (81, 1),
         (79, .5), (77, .5), (76, 1), (73, 1), (69, 1)]
MEL_A2 = MEL_A[:-5] + [(79, .5), (77, .5), (76, 1), (73, 1), (74, 1)]
MEL_B = [(81, 2), (79, .5), (77, .5), (76, 1),
         (79, 1.5), (77, .5), (76, 1), (74, 1),
         (77, 1), (74, 1), (77, 1), (79, 1),
         (81, 1), (79, .5), (77, .5), (76, 2)]
MEL_C = [(84, 1), (81, 1), (77, 1), (81, 1),
         (79, 2), (76, 1), (79, 1),
         (81, 1), (77, 1), (86, 1), (84, 1),
         (82, 2), (81, 1), (79, 1)]
MEL_END = [(81, 1), (79, .5), (77, .5), (76, 1), (73, 1),
           (74, 4)]

# Bo'limlar (taktlarda): (taktlar soni, progressiya, kuy, zichlik)
#   zichlik: 0 — faqat fon+dutor, 1 — yengil doira, 2 — to'liq
FORM = [
    (4, ANDALUS, None, 0),          # 0–10 s   kirish
    (4, ANDALUS, MEL_A, 1),         # 10–20 s
    (4, ANDALUS, MEL_A2, 1),        # 20–30 s
    (4, ANDALUS, MEL_B, 1),         # 30–40 s
    (4, ANDALUS, MEL_A2, 2),        # 40–50 s
    (4, ANDALUS, MEL_B, 2),         # 50–60 s
    (4, ANDALUS, MEL_A, 2),         # 60–70 s
    (4, ANDALUS, MEL_A2, 2),        # 70–80 s
    (4, ANDALUS, MEL_B, 2),         # 80–90 s
    (4, ANDALUS, MEL_A2, 2),        # 90–100 s
    (4, LIFT, MEL_C, 2),            # 100–110 s  yorug' ko'tarilish
    (4, LIFT, MEL_C, 2),            # 110–120 s
    (4, LIFT, MEL_B, 2),            # 120–130 s
    (4, ANDALUS, MEL_A2, 1),        # 130–140 s  final
    (4, ["Dm", "Bb", "Gm", "Dm"], MEL_END, 0),  # 140–150 s  muallif sahnasi, sokin yakun
]

DOIRA = ["D", None, "t", "t", "D", "t", None, "t"]  # 8-taliklar, bir takt


def compose(duration=150.0):
    n = int(SR * (duration + 4))
    bus = {k: np.zeros(n) for k in ("pluck", "flute", "pad", "drum", "bass")}

    def add(track, sig, at, gain=1.0):
        i = int(at * SR)
        if i >= n:
            return
        sig = sig[: n - i]
        bus[track][i:i + len(sig)] += sig * gain

    t0 = 0.0
    for bars, prog, mel, dens in FORM:
        for b in range(bars):
            name = prog[b % len(prog)]
            ch = CH[name]
            at = t0 + b * BAR
            add("pad", pad([c + 12 for c in ch[1:]], BAR + 0.6), at, 0.55 if dens else 0.75)
            # Dutor arpedjiosi (8-taliklar)
            arp = [ch[0] + 12, ch[1] + 12, ch[2] + 12, ch[3] + 12, ch[2] + 12, ch[1] + 12, ch[3] + 12, ch[2] + 12]
            for k, m in enumerate(arp):
                acc = 1.0 if k % 2 == 0 else 0.7
                add("pluck", pluck(m, 1.4, acc, 0.55), at + k * BEAT / 2, 0.55)
            if dens >= 1:
                root = ch[0] if ch[0] < 48 else ch[0] - 12  # bas 43–55 MIDI oralig'ida
                root = root + 12 if root < 40 else root
                add("bass", pluck(root, 2.2, 1.0, 0.25), at, 0.9)
                add("bass", pluck(root, 1.6, 0.8, 0.25), at + 2.5 * BEAT, 0.8)
                for k, hit in enumerate(DOIRA):
                    ht = at + k * BEAT / 2
                    if hit == "D":
                        add("drum", dum(1.0), ht, 0.8 if dens == 2 else 0.55)
                    elif hit == "t":
                        add("drum", tak(0.8 + 0.2 * rng.random()), ht, 0.32 if dens == 2 else 0.2)
                    if dens == 2 and k % 2 == 1:
                        add("drum", zil(0.6), ht, 0.10)
        if mel:
            pos = t0
            for m, beats in mel:
                d = beats * BEAT
                if m is not None:
                    add("flute", flute(m, d + 0.12, 1.0), pos, 0.30)
                pos += d
        t0 += bars * BAR

    mix = (bus["pluck"] * 0.9 + bus["flute"] * 1.15 + bus["pad"] * 0.55 + bus["drum"] * 0.55 + bus["bass"] * 0.4)
    # Stereo: dutor va doira biroz kengaytiriladi
    left = mix + bus["pluck"] * 0.15 - bus["drum"] * 0.05
    right = mix - bus["pluck"] * 0.15 + bus["drum"] * 0.05
    st = np.stack([left, right])
    # Past chastotalarni tozalash (g'o'ng'illashning oldini olish)
    st = sosfilt(butter(2, 55, "highpass", fs=SR, output="sos"), st, axis=1)
    # Reverb: sintetik impuls javobi (2.4 s)
    ir_n = int(SR * 2.4)
    tt = np.arange(ir_n) / SR
    ir = rng.normal(0, 1, (2, ir_n)) * np.exp(-tt * 2.6)
    ir = sosfilt(butter(1, 5000, "lowpass", fs=SR, output="sos"), ir, axis=1)
    ir /= np.abs(ir).sum(axis=1, keepdims=True) / 6
    wet = np.stack([fftconvolve(st[c], ir[c])[:n] for c in range(2)])
    out = st * 0.82 + wet * 0.30
    out = out[:, : int(SR * duration)]
    tt = np.arange(out.shape[1]) / SR
    out *= np.minimum(1, tt / 1.5) * np.clip((duration - tt) / 5.0, 0, 1)
    out /= np.abs(out).max() / 0.89
    return out


def write_wav(out, path):
    pcm = (np.clip(out.T, -1, 1) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--duration", type=float, default=150.0)
    a = ap.parse_args()
    write_wav(compose(a.duration), a.out)
