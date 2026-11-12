#!/usr/bin/env python3
"""Aggregates benchmark results and runs the correctness cross-check.

Input:    results/neve*.csv (single-line blob, printl emits no \n; one file per run),
          results/librosa*.csv, results/torchaudio*.csv (real CSV; one file per run),
          results/rss.csv (peak RSS per implementation, written by run_with_rss.py),
          results/out_neve_*.wav (Neve lib f32 outputs),
          results/out_<impl>_*.npy (reference outputs).
Output:   results/summary.csv, results/accuracy.csv and console tables.
With several runs per implementation the tables report the median of the per-run
means; summary.csv also carries the min-max range of those means.
"""
import csv
import glob
import os
import re

import numpy as np
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.environ.get("NEVE_AUDIO_BENCH_RESULTS", os.path.join(HERE, "results"))

ROWS = []  # (impl, op, signal, threads, iters, mean, min)


# Neve prints floats with exactly 6 decimals. The release binary also prints debug lines to stdout,
# which can be glued right after a record (sometimes starting with digits), so read exactly that format.
NEVE_REC = re.compile(r"([a-z0-9_]+),([a-z0-9_]+),(1T|defT),(\d+),(-?\d+\.\d{6}),(-?\d+\.\d{6})")


def parse_neve_blob(path):
    blob = open(path).read()
    # each record starts with "neve,"; anything else (header, debug noise) is ignored
    for chunk in blob.split("neve,")[1:]:
        m = NEVE_REC.match(chunk)
        if m:
            op, sig, th, iters, mean, mn = m.groups()
            ROWS.append(("neve", op, sig, th, int(iters), float(mean), float(mn)))


def parse_py_csv(path):
    impl = os.path.basename(path).split("_")[0]
    with open(path) as f:
        for row in csv.reader(f):
            if len(row) != 7 or row[0] == "impl":
                continue
            ROWS.append((row[0], row[1], row[2], row[3], int(row[4]), float(row[5]), float(row[6])))


def load_inputs():
    for p in sorted(glob.glob(os.path.join(RES, "neve*.csv"))):
        parse_neve_blob(p)
    for p in sorted(glob.glob(os.path.join(RES, "librosa*.csv"))):
        parse_py_csv(p)
    for p in sorted(glob.glob(os.path.join(RES, "torchaudio*.csv"))):
        parse_py_csv(p)


def summary():
    """summary.csv + timing table (threads=1T): median of the per-run means, with the run range."""
    by = {}
    for impl, op, sig, th, iters, mean, mn in ROWS:
        if th not in ("1T", "defT"):
            continue
        by.setdefault((op, sig, th), {}).setdefault(impl, []).append(mean)
    med = lambda v: float(np.median(v)) if v else None
    rng = lambda v: f"{min(v):.4f}-{max(v):.4f}" if v else ""
    out = os.path.join(RES, "summary.csv")
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["op", "signal", "threads", "neve_ms", "librosa_ms", "torchaudio_ms",
                    "neve_vs_librosa", "neve_vs_torchaudio", "runs",
                    "neve_range", "librosa_range", "torchaudio_range"])
        print("\n== TIMING (ms_mean, median over runs) ==\n")
        print(f"{'op':<18} {'signal':<16} {'neve':>10} {'librosa':>10} {'torchaudio':>10} "
              f"{'vs_librosa':>10} {'vs_taudio':>10} {'runs':>5}")
        for (op, sig, th) in sorted(by):
            d = by[(op, sig, th)]
            nv, li, ta = med(d.get("neve")), med(d.get("librosa")), med(d.get("torchaudio"))
            sli = f"{li / nv:.2f}x" if nv and li else "-"
            sta = f"{ta / nv:.2f}x" if nv and ta else "-"
            runs = max(len(v) for v in d.values())
            fmt = lambda v: (f"{v:>10.3f}" if v is not None else f"{'-':>10}")
            w.writerow([op, sig, th,
                        f"{nv:.4f}" if nv is not None else "", f"{li:.4f}" if li is not None else "",
                        f"{ta:.4f}" if ta is not None else "", sli, sta, runs,
                        rng(d.get("neve")), rng(d.get("librosa")), rng(d.get("torchaudio"))])
            if th == "1T":
                print(f"{op:<18} {sig:<16} {fmt(nv)} {fmt(li)} {fmt(ta)} "
                      f"{sli:>10} {sta:>10} {runs:>5}")
    print(f"\nsummary -> {out}")


def rss_report():
    """Peak resident memory per implementation (max over runs), from results/rss.csv."""
    p = os.path.join(RES, "rss.csv")
    if not os.path.exists(p):
        return
    peak = {}
    with open(p) as f:
        for row in csv.reader(f):
            if len(row) == 4 and row[0] != "impl":
                key = (row[0], row[1])
                peak[key] = max(peak.get(key, 0.0), float(row[3]))
    print("\n== PEAK RSS (MB, max over runs; includes the interpreter / compiler) ==\n")
    for (impl, th), mb in sorted(peak.items()):
        print(f"{impl:<12} {th:<5} {mb:>10.1f}")


def pearson(a, b):
    a = a.astype(np.float64).ravel()
    b = b.astype(np.float64).ravel()
    if a.shape != b.shape:
        return float("nan")
    ca, cb = a - a.mean(), b - b.mean()
    denom = np.sqrt((ca ** 2).sum() * (cb ** 2).sum())
    return float((ca * cb).sum() / denom) if denom > 0 else 0.0


def snr(a, b):
    a = a.astype(np.float64).ravel()
    b = b.astype(np.float64).ravel()
    if a.shape != b.shape:
        return float("nan")
    e = ((a - b) ** 2).sum()
    s = (b ** 2).sum()
    return float(10 * np.log10(s / e)) if e > 0 else 120.0


def rel_diff(a, b):
    a = a.astype(np.float64).ravel()
    b = b.astype(np.float64).ravel()
    if a.shape != b.shape:
        return float("nan")
    den = np.abs(b).max() + 1e-12
    return float(np.abs(a - b).max() / den)


def neve_wav(name, ref_shape=None):
    p = os.path.join(RES, f"out_neve_{name}.wav")
    if not os.path.exists(p):
        return None
    d, _ = sf.read(p, dtype="float32")
    # audio_save interleaves per frame: [C,T] -> flat[(t*C+c)]. For 2D refs
    # (bins x frames), reorder to numpy row-major order.
    if ref_shape is not None and len(ref_shape) == 2:
        bins, frames = ref_shape
        if d.size == bins * frames:
            d = d.reshape(frames, bins).T
    return d


def npy(impl, name):
    p = os.path.join(RES, f"out_{impl}_{name}.npy")
    if not os.path.exists(p):
        return None
    a = np.load(p)
    return np.squeeze(a)


def spectral_convergence(a, b):
    """||(|S_a| - |S_b|)||_F / ||S_b||_F of the two signals' STFTs (n_fft 1024, hop 256)."""
    import librosa
    kw = dict(n_fft=1024, hop_length=256, window="hann")
    sa = np.abs(librosa.stft(a.astype(np.float32), **kw))
    sb = np.abs(librosa.stft(b.astype(np.float32), **kw))
    return float(np.linalg.norm(sa - sb) / np.linalg.norm(sb))


def load_fidelity():
    """audio_load must reproduce soundfile's float32 samples bit for bit."""
    print("\n== LOAD FIDELITY (Neve vs soundfile, bit-exact) ==\n")
    cases = [("load_s16", "sig_10s_16k_s16.wav"), ("load_f32", "sig_10s_16k_f32.wav"),
             ("load_f32_stereo", "sig_10s_22k_stereo_f32.wav")]
    rows = []
    for name, wav in cases:
        got = neve_wav(name)
        if got is None:
            continue
        ref, _ = sf.read(os.path.join(HERE, "data", wav), dtype="float32")
        ok = got.shape == ref.shape and np.array_equal(got, ref)
        maxdiff = float(np.abs(got - ref).max()) if got.shape == ref.shape else float("nan")
        print(f"{name:<16} {'max abs diff':<14} {maxdiff:>12.6g} {'OK' if ok else 'CHECK':>8}")
        rows.append([name, "soundfile", "max abs diff", f"{maxdiff:.6g}", "OK" if ok else "CHECK"])
    return rows


def accuracy():
    checks = [
        # (name, metric_fn, tolerance, description). Measured: 114-135 dB, so 110 catches real regressions.
        ("spectrogram", lambda a, b: snr(a, b), 110.0, "SNR dB (min)"),
        ("mel", lambda a, b: snr(a, b), 110.0, "SNR dB (min)"),
        ("mfcc", lambda a, b: snr(a, b), 110.0, "SNR dB (min)"),
        ("resample8k", lambda a, b: snr(a, b), 40.0, "SNR dB (min)"),
        ("resample24k", lambda a, b: snr(a, b), 38.0, "SNR dB (min)"),
        ("mulaw", None, 0, "max decoded diff"),
        ("stretch", None, 0, "SNR + convergence"),
    ]
    out = os.path.join(RES, "accuracy.csv")
    print("\n== CORRECTNESS (Neve vs reference) ==\n")
    print(f"{'op':<14} {'ref':<11} {'metric':<22} {'value':>12} {'status':>8}")
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["op", "ref", "metric", "value", "status"])
        for name, fn, tol, desc in checks:
            ref0 = npy("librosa", name)
            if ref0 is None:
                ref0 = npy("torchaudio", name)
            rs = ref0.shape if ref0 is not None else None
            nv = neve_wav(name, rs)
            if nv is None:
                continue
            for impl in ("librosa", "torchaudio"):
                ref = npy(impl, name)
                if ref is None:
                    continue
                if name == "stretch":
                    # The three implementations run the same phase vocoder (n_fft 1024, hop 256), so the
                    # waveforms must agree, not just the duration.
                    ratio = len(nv) / max(len(ref.ravel()), 1)
                    n = min(len(nv), len(ref.ravel()))
                    val_snr = snr(nv[:n], ref.ravel()[:n])
                    val_sc = spectral_convergence(nv[:n], ref.ravel()[:n])
                    # librosa accumulates the phase unwrapped in float32 (~29 dB from a float64 reference
                    # at rate 1.5); torchaudio and Neve agree with that reference to ~52 dB.
                    min_snr = 40.0 if impl == "torchaudio" else 25.0
                    for metric, v, good in (("len_ratio", ratio, abs(ratio - 1.0) < 0.001),
                                            ("SNR dB (min)", val_snr, val_snr >= min_snr),
                                            ("spectral convergence", val_sc, val_sc <= 0.01)):
                        w.writerow([name, impl, metric, f"{v:.4f}", "OK" if good else "CHECK"])
                        print(f"{name:<14} {impl:<11} {metric:<22} {v:>12.4f} {'OK' if good else 'CHECK':>8}")
                elif name == "mulaw":
                    # code conventions differ between impls: compare the decoded audio
                    c_neve = nv.ravel().astype(np.int32)
                    s = (c_neve >> 7) & 1
                    mag = c_neve & 127
                    ax = ((1.0 + 255.0) ** (mag / 127.0) - 1.0) / 255.0
                    dec_neve = np.where(s == 1, -ax, ax).astype(np.float64)
                    try:
                        if impl == "librosa":
                            import librosa
                            dec_ref = librosa.mu_expand(ref.ravel().astype(np.float64), mu=255)
                        else:
                            import torch
                            import torchaudio.functional as AF
                            dec_ref = AF.mu_law_decoding(
                                torch.from_numpy(ref.ravel().astype(np.float32)),
                                quantization_channels=256).numpy()
                        val = (float(np.abs(dec_neve - dec_ref).max())
                               if len(dec_neve) == len(dec_ref) else -1.0)
                    except Exception as e:
                        val = -1.0
                    ok = 0 <= val <= 0.06
                    w.writerow([name, impl, desc, f"{val:.6f}", "OK" if ok else "CHECK"])
                    print(f"{name:<14} {impl:<11} {desc:<22} {val:>12.6f} {'OK' if ok else 'CHECK':>8}")
                else:
                    val = fn(nv, ref)
                    effective_tol = tol
                    ok = (val <= effective_tol) if "diff" in desc else (val >= effective_tol)
                    w.writerow([name, impl, desc, f"{val:.6f}", "OK" if ok else "CHECK"])
                    print(f"{name:<14} {impl:<11} {desc:<22} {val:>12.6f} {'OK' if ok else 'CHECK':>8}")
        for row in load_fidelity():
            w.writerow(row)
    print(f"\naccuracy -> {out}")


if __name__ == "__main__":
    load_inputs()
    print(f"loaded records: {len(ROWS)}")
    summary()
    rss_report()
    accuracy()
