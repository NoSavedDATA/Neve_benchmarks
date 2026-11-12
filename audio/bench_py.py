#!/usr/bin/env python3
"""Python-side benchmark: librosa and torchaudio (CPU).

Mirrors bench_neve.nv: same signals, same parameters, same CSV
"<impl>,<op>,<signal>,<threads>,<iters>,<ms_mean>,<ms_min>" (one line per
record, with real newlines). 3 warm-up iterations discarded.
Writes reference outputs to results/out_<impl>_<op>.npy for the merge.
"""
import argparse
import os
import time
import tempfile
import numpy as np
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
RES = os.environ.get("NEVE_AUDIO_BENCH_RESULTS", os.path.join(HERE, "results"))
os.makedirs(RES, exist_ok=True)

N_FFT, HOP, N_MELS, N_MFCC = 1024, 256, 128, 20


def emit(impl, op, sig, threads, iters, mean, mn):
    print(f"{impl},{op},{sig},{threads},{iters},{mean:.6f},{mn:.6f}")


def bench(fn, iters, impl, op, sig, threads):
    times = []
    for i in range(iters + 3):
        t0 = time.perf_counter_ns()
        out = fn()
        dt = (time.perf_counter_ns() - t0) / 1e6
        if i >= 3:
            times.append(dt)
    a = np.array(times)
    emit(impl, op, sig, threads, iters, float(a.mean()), float(a.min()))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--impl", choices=["librosa", "torchaudio"], required=True)
    ap.add_argument("--threads", choices=["1", "default"], default="1")
    args = ap.parse_args()
    th = "1T" if args.threads == "1" else "defT"

    if args.threads == "1":
        os.environ["OMP_NUM_THREADS"] = "1"
        os.environ["MKL_NUM_THREADS"] = "1"
        os.environ["NUMEXPR_NUM_THREADS"] = "1"

    print("impl,op,signal,threads,iters,ms_mean,ms_min")

    signals = {
        "1s_16k": "sig_1s_16k_s16.wav",
        "10s_16k": "sig_10s_16k_s16.wav",
        "10s_16k_f32": "sig_10s_16k_f32.wav",
        "60s_16k": "sig_60s_16k_s16.wav",
        "10s_22k_stereo": "sig_10s_22k_stereo_f32.wav",
    }
    paths = {k: os.path.join(DATA, v) for k, v in signals.items()}
    with tempfile.NamedTemporaryFile(dir=RES, suffix=".wav", delete=False) as tmp:
        save_path = tmp.name

    if args.impl == "librosa":
        import librosa
        import scipy.signal

        HANN_SYM = scipy.signal.windows.hann(N_FFT, sym=True)

        def load(sig, mono=True):
            return lambda: librosa.load(paths[sig], sr=None, mono=mono)

        y10, sr10 = librosa.load(paths["10s_16k"], sr=None)
        y60, _ = librosa.load(paths["60s_16k"], sr=None)

        bench(load("1s_16k"), 50, "librosa", "load_s16", "1s_16k", th)
        bench(load("10s_16k"), 50, "librosa", "load_s16", "10s_16k", th)
        bench(load("10s_16k_f32"), 50, "librosa", "load_f32", "10s_16k", th)
        bench(load("60s_16k"), 20, "librosa", "load_s16", "60s_16k", th)
        bench(load("10s_22k_stereo", mono=False), 50, "librosa", "load_f32", "10s_22k_stereo", th)

        def save16():
            sf.write(save_path, y10, sr10, subtype="PCM_16")
        bench(save16, 50, "librosa", "save_s16", "10s_16k", th)

        def spec(y):
            return lambda: np.abs(librosa.stft(y, n_fft=N_FFT, hop_length=HOP,
                                               win_length=N_FFT, window=HANN_SYM, center=True, pad_mode="reflect")) ** 2
        sp10 = bench(spec(y10), 20, "librosa", "spectrogram", "10s_16k", th)
        np.save(os.path.join(RES, "out_librosa_spectrogram.npy"), sp10)
        bench(spec(y60), 10, "librosa", "spectrogram", "60s_16k", th)

        def mel(y):
            return lambda: librosa.feature.melspectrogram(
                y=y, sr=sr10, n_fft=N_FFT, hop_length=HOP, n_mels=N_MELS,
                fmin=0.0, fmax=sr10 / 2, power=2.0, htk=True,
                norm=None, window=HANN_SYM, pad_mode="reflect")
        m10 = bench(mel(y10), 20, "librosa", "mel", "10s_16k", th)
        np.save(os.path.join(RES, "out_librosa_mel.npy"), m10)
        bench(mel(y60), 10, "librosa", "mel", "60s_16k", th)

        def mfcc(y):
            return lambda: librosa.feature.mfcc(y=y, sr=sr10, n_mfcc=N_MFCC,
                                                n_fft=N_FFT, hop_length=HOP, n_mels=N_MELS,
                                                htk=True, mel_norm=None,
                                                window=HANN_SYM, pad_mode="reflect")
        f10 = bench(mfcc(y10), 20, "librosa", "mfcc", "10s_16k", th)
        np.save(os.path.join(RES, "out_librosa_mfcc.npy"), f10)

        def resample(y, new_sr, res_type):
            return lambda: librosa.resample(y, orig_sr=sr10, target_sr=new_sr, res_type=res_type)
        r8 = bench(resample(y10, 8000, "soxr_hq"), 20, "librosa", "resample_sinc", "10s_16k", th)
        np.save(os.path.join(RES, "out_librosa_resample8k.npy"), r8)
        bench(resample(y10, 8000, "soxr_lq"), 20, "librosa", "resample_soxr_lq", "10s_16k", th)
        r24 = bench(resample(y10, 24000, "soxr_hq"), 20, "librosa", "resample_sinc", "10s_16k_24k", th)
        np.save(os.path.join(RES, "out_librosa_resample24k.npy"), r24)

        def mulaw(y):
            return lambda: librosa.mu_compress(y, mu=255, quantize=True).astype(np.float32)
        mu = bench(mulaw(y10), 100, "librosa", "mulaw_encode", "10s_16k", th)
        np.save(os.path.join(RES, "out_librosa_mulaw.npy"), mu)

        def stretch():
            # Same STFT configuration as Neve and torchaudio: n_fft 1024, hop 256, symmetric Hann, reflect
            # padding. (librosa.effects.time_stretch uses n_fft=2048/hop=512 and zero padding by default, and
            # cannot pass pad_mode to its istft.)
            S = librosa.stft(y10, n_fft=N_FFT, hop_length=HOP, win_length=N_FFT, window=HANN_SYM,
                             center=True, pad_mode="reflect")
            S = librosa.phase_vocoder(S, rate=1.5, hop_length=HOP, n_fft=N_FFT)
            return librosa.istft(S, hop_length=HOP, win_length=N_FFT, n_fft=N_FFT, window=HANN_SYM,
                                 length=round(len(y10) / 1.5))
        st = bench(stretch, 10, "librosa", "time_stretch", "10s_16k", th)
        np.save(os.path.join(RES, "out_librosa_stretch.npy"), st)

    else:  # torchaudio
        import torch
        import torchaudio
        import torchaudio.functional as AF
        import torchaudio.transforms as AT

        try:
            torchaudio.set_audio_backend("soundfile")
        except Exception:
            pass  # the default backend (sox/soundfile) works
        if args.threads == "1":
            torch.set_num_threads(1)

        dev = "cpu"

        def symmetric_hann(n):
            return torch.hann_window(n, periodic=False)

        def load(sig):
            return lambda: torchaudio.load(paths[sig])[0]

        t10 = bench(load("1s_16k"), 50, "torchaudio", "load_s16", "1s_16k", th)
        w10 = bench(load("10s_16k"), 50, "torchaudio", "load_s16", "10s_16k", th)
        bench(load("10s_16k_f32"), 50, "torchaudio", "load_f32", "10s_16k", th)
        w60 = bench(load("60s_16k"), 20, "torchaudio", "load_s16", "60s_16k", th)
        bench(load("10s_22k_stereo"), 50, "torchaudio", "load_f32", "10s_22k_stereo", th)

        def save16():
            torchaudio.save(save_path, w10, 16000, encoding="PCM_S", bits_per_sample=16)
        bench(save16, 50, "torchaudio", "save_s16", "10s_16k", th)

        spec_t = AT.Spectrogram(n_fft=N_FFT, hop_length=HOP, win_length=N_FFT,
                                power=2.0, center=True, window_fn=symmetric_hann).to(dev)

        def spec(w):
            return lambda: spec_t(w).numpy()
        sp10 = bench(spec(w10), 20, "torchaudio", "spectrogram", "10s_16k", th)
        np.save(os.path.join(RES, "out_torchaudio_spectrogram.npy"), sp10)
        bench(spec(w60), 10, "torchaudio", "spectrogram", "60s_16k", th)

        mel_t = AT.MelSpectrogram(sample_rate=16000, n_fft=N_FFT, hop_length=HOP,
                                  n_mels=N_MELS, f_min=0.0, f_max=8000.0,
                                  power=2.0, mel_scale="htk", window_fn=symmetric_hann).to(dev)

        def mel(w):
            return lambda: mel_t(w).numpy()
        m10 = bench(mel(w10), 20, "torchaudio", "mel", "10s_16k", th)
        np.save(os.path.join(RES, "out_torchaudio_mel.npy"), m10)
        bench(mel(w60), 10, "torchaudio", "mel", "60s_16k", th)

        mfcc_t = AT.MFCC(sample_rate=16000, n_mfcc=N_MFCC,
                         melkwargs={"n_fft": N_FFT, "hop_length": HOP, "n_mels": N_MELS,
                                    "f_min": 0.0, "f_max": 8000.0, "mel_scale": "htk", "window_fn": symmetric_hann}).to(dev)

        def mfcc(w):
            return lambda: mfcc_t(w).numpy()
        f10 = bench(mfcc(w10), 20, "torchaudio", "mfcc", "10s_16k", th)
        np.save(os.path.join(RES, "out_torchaudio_mfcc.npy"), f10)

        def resample(new_sr):
            r = AT.Resample(orig_freq=16000, new_freq=new_sr).to(dev)
            return lambda: r(w10).numpy()
        r8 = bench(resample(8000), 20, "torchaudio", "resample_sinc", "10s_16k", th)
        np.save(os.path.join(RES, "out_torchaudio_resample8k.npy"), r8)
        r24 = bench(resample(24000), 20, "torchaudio", "resample_sinc", "10s_16k_24k", th)
        np.save(os.path.join(RES, "out_torchaudio_resample24k.npy"), r24)

        def mulaw(w):
            return lambda: AF.mu_law_encoding(w, quantization_channels=256).numpy()
        mu = bench(mulaw(w10), 100, "torchaudio", "mulaw_encode", "10s_16k", th)
        np.save(os.path.join(RES, "out_torchaudio_mulaw.npy"), mu)

        spec_c = AT.Spectrogram(n_fft=N_FFT, hop_length=HOP, win_length=N_FFT,
                                power=None, center=True, window_fn=symmetric_hann).to(dev)
        synth_window = symmetric_hann(N_FFT).to(dev)

        def stretch():
            w = w10.to(dev)
            S = spec_c(w)
            ph_adv = torch.linspace(0, np.pi * HOP, S.shape[-2], device=dev)[None, :, None]
            stretched = AF.phase_vocoder(S, rate=1.5, phase_advance=ph_adv)
            return torch.istft(stretched, n_fft=N_FFT, hop_length=HOP,
                               window=synth_window, length=round(w.shape[-1] / 1.5)).numpy()
        st = bench(stretch, 10, "torchaudio", "time_stretch", "10s_16k", th)
        np.save(os.path.join(RES, "out_torchaudio_stretch.npy"), st)

    assert sf.info(save_path).subtype == "PCM_16"
    os.unlink(save_path)


if __name__ == "__main__":
    main()
