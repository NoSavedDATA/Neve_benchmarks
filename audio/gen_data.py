#!/usr/bin/env python3
"""Generates the benchmark test signals (neutral: soundfile/numpy).

The WAVs are read by all three sides (neve audio_load, librosa, torchaudio).
Prints a checksum (sample sum) for cross-checking.
"""
import numpy as np
import soundfile as sf
import os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(42)


def make_signal(sr, seconds):
    t = np.arange(int(sr * seconds), dtype=np.float64) / sr
    x = 0.5 * np.sin(2 * np.pi * 440.0 * t)
    x += 0.25 * np.sin(2 * np.pi * 880.0 * t + 0.3)
    x += 0.125 * np.sin(2 * np.pi * 1320.0 * t + 1.1)
    # noise bursts every 0.7 s
    n = len(x)
    for start in range(0, n, int(0.7 * sr)):
        dur = int(0.05 * sr)
        seg = slice(start, min(start + dur, n))
        x[seg] += 0.1 * rng.standard_normal(seg.stop - seg.start)
    peak = np.max(np.abs(x))
    return (x / peak * 0.9).astype(np.float32)


signals = [
    ("sig_1s_16k_s16.wav", 16000, 1.0, "PCM_16", False),
    ("sig_10s_16k_s16.wav", 16000, 10.0, "PCM_16", False),
    ("sig_10s_16k_f32.wav", 16000, 10.0, "FLOAT", False),
    ("sig_60s_16k_s16.wav", 16000, 60.0, "PCM_16", False),
    ("sig_10s_22k_stereo_f32.wav", 22050, 10.0, "FLOAT", True),
]

for name, sr, secs, subtype, stereo in signals:
    x = make_signal(sr, secs)
    if stereo:
        # right channel slightly delayed and attenuated
        delay = int(0.004 * sr)
        right = np.concatenate([np.zeros(delay, dtype=np.float32), x[:-delay]]) * 0.8
        x = np.stack([x, right], axis=1)  # soundfile: (samples, channels)
    path = os.path.join(OUT, name)
    sf.write(path, x, sr, subtype=subtype, format="WAV")
    checksum = float(np.sum(x, dtype=np.float64))
    print(f"{name}: sr={sr} shape={x.shape} subtype={subtype} checksum={checksum:.6f}")

print("done ->", OUT)
