"""Qo'shiqdan vokalni olib tashlash (minus / instrumental) — MDX-Net (UVR Inst HQ3, ONNX).

    python video/separate.py song.mp3 out.wav --model UVR-MDX-NET-Inst_HQ_3.onnx

Model: https://github.com/TRvlvr/model_repo/releases (UVR jamoasi, ochiq).
STFT/ISTFT numpy'da torch.stft(center=True, reflect) bilan bir xil tarzda bajariladi.
"""
import argparse
import subprocess
import wave

import numpy as np
import onnxruntime as ort

N_FFT, HOP, DIM_F, DIM_T = 6144, 1024, 3072, 256
COMPENSATE = 1.022
CHUNK = HOP * (DIM_T - 1)
TRIM = N_FFT // 2
GEN = CHUNK - 2 * TRIM
WIN = np.hanning(N_FFT + 1)[:-1].astype(np.float32)  # periodic hann (torch.hann_window)


def stft(x):
    """x: (ch, CHUNK) -> (ch, N_FFT//2+1, DIM_T) complex."""
    pad = N_FFT // 2
    xp = np.pad(x, ((0, 0), (pad, pad)), mode="reflect")
    idx = np.arange(DIM_T)[:, None] * HOP + np.arange(N_FFT)[None, :]
    frames = xp[:, idx] * WIN  # (ch, T, N_FFT)
    return np.fft.rfft(frames, axis=-1).transpose(0, 2, 1)


def istft(spec):
    """spec: (ch, F, T) complex -> (ch, CHUNK)."""
    frames = np.fft.irfft(spec.transpose(0, 2, 1), n=N_FFT, axis=-1) * WIN
    length = N_FFT + HOP * (DIM_T - 1)
    out = np.zeros((spec.shape[0], length), np.float32)
    norm = np.zeros(length, np.float32)
    for t in range(DIM_T):
        s = t * HOP
        out[:, s:s + N_FFT] += frames[:, t]
        norm[s:s + N_FFT] += WIN ** 2
    out /= np.maximum(norm, 1e-8)
    pad = N_FFT // 2
    return out[:, pad:pad + CHUNK]


def run(sess, mix):
    n = mix.shape[1]
    pad_r = GEN - n % GEN
    mix_p = np.concatenate([np.zeros((2, TRIM), np.float32), mix, np.zeros((2, pad_r + TRIM), np.float32)], axis=1)
    out = []
    for i in range(0, n + pad_r, GEN):
        spec = stft(mix_p[:, i:i + CHUNK])[:, :DIM_F]  # (2, 3072, 256)
        inp = np.stack([spec.real, spec.imag], axis=1).reshape(1, 4, DIM_F, DIM_T).astype(np.float32)
        res = sess.run(None, {"input": inp})[0].reshape(2, 2, DIM_F, DIM_T)
        cspec = np.zeros((2, N_FFT // 2 + 1, DIM_T), np.complex64)
        cspec[:, :DIM_F] = res[:, 0] + 1j * res[:, 1]
        out.append(istft(cspec)[:, TRIM:-TRIM])
        print(f"{min(100, int(100 * (i + GEN) / (n + pad_r)))}%", flush=True)
    return np.concatenate(out, axis=1)[:, :n] * COMPENSATE


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--model", required=True)
    a = ap.parse_args()
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", a.src, "-f", "f32le", "-ac", "2", "-ar", "44100", "-"],
                         capture_output=True, check=True).stdout
    mix = np.frombuffer(raw, np.float32).reshape(-1, 2).T.copy()
    sess = ort.InferenceSession(a.model, providers=["CPUExecutionProvider"])
    inst = run(sess, mix)
    pcm = (np.clip(inst.T, -1, 1) * 32767).astype("<i2")
    with wave.open(a.dst, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(44100)
        w.writeframes(pcm.tobytes())


if __name__ == "__main__":
    main()
