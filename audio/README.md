# Audio Processing: Neve vs librosa vs torchaudio

CPU-only comparison between the Neve [audio library](https://github.com/freds0/audio)
(`import audio`) and its Python equivalents, [librosa](https://librosa.org/) and
[torchaudio](https://pytorch.org/audio/): WAV load/save, spectrogram, mel spectrogram,
MFCC, sinc resampling, μ-law encoding and time stretch.

## Requirements

- Docker
- x86-64 host (no GPU needed)

Tested inside Linux, you may adapt pre-docker steps

---
## Install Steps

```bash
cd ~/
git clone https://github.com/NoSavedDATA/Neve_benchmarks.git
cd Neve_benchmarks/audio
docker build -t neve-audio .
docker run --rm -v ~/Neve_benchmarks:/frost_exp/Neve_benchmarks -it neve-audio bash
```

The image installs Neve, the audio library (`nsm i freds0/audio`) and the Python packages.

Generate the test signals (440 Hz sine + harmonics + noise bursts, fixed seed) in `data/`
```bash
./setup.sh
```

Neve evaluation
```bash
neve bench_neve.nv > results/neve.csv
```

Python evaluation
```bash
python3 bench_py.py --impl librosa --threads 1 > results/librosa_1.csv
python3 bench_py.py --impl torchaudio --threads 1 > results/torchaudio_1.csv
```

Tables and correctness cross-check (Neve outputs vs the Python references)
```bash
python3 merge.py
```

Or run everything: 3 repetitions, one pinned core plus a default-threads Python column,
peak RSS per process, then the merge
```bash
./run.sh
```

Results land in `results/` (`summary.csv`, `accuracy.csv`, `rss.csv`).

---
## Methodology

- Parameters: `n_fft=1024`, `hop=256`, Hann window, `center=True` (reflection padding),
  `n_mels=128`, `n_mfcc=20`, power 2.0, μ-law with 255 levels, 1.5× stretch.
  librosa's mel/MFCC use `htk=True` and no filter normalization, matching the Neve lib.
- 3 warm-up calls discarded (librosa's first call triggers numba JIT). Neve times with
  `audio_tic()`/`audio_toc()` and measures sub-millisecond ops in batches of 10; Python uses
  `time.perf_counter_ns` per call, so only `ms_mean` is comparable between the two sides.
- 1T column: `OMP_NUM_THREADS=1`, `torch.set_num_threads(1)`, pinned with `taskset`
  (the Neve kernels are sequential).
- Correctness: Neve writes each output as a float32 WAV and `merge.py` compares it with
  the Python outputs (SNR, max difference, bit-exact loads).

---
## Results

One core (i7-7700, Docker), median of 3 runs, mean milliseconds per call,
10 s mono 16 kHz unless stated. Bold = fastest.

| Operation | Neve | librosa | torchaudio | Neve vs fastest Python |
| :--- | ---: | ---: | ---: | ---: |
| load PCM16, 1 s | **0.053** | 0.141 | 0.149 | 2.64× |
| load PCM16 | **0.316** | 0.511 | 0.512 | 1.62× |
| load PCM16, 60 s | **1.836** | 2.881 | 2.534 | 1.38× |
| load f32 | 0.238 | 0.184 | **0.155** | 0.65× |
| load f32, stereo 22 kHz | 0.916 | **0.236** | 0.255 | 0.26× |
| save PCM16 | **1.616** | 12.744 | 11.736 | 7.26×\* |
| spectrogram | **2.307** | 4.231 | 3.494 | 1.51× |
| spectrogram, 60 s | **13.220** | 24.289 | 26.121 | 1.84× |
| mel | **1.736** | 6.087 | 4.165 | 2.40× |
| mel, 60 s | **10.524** | 30.907 | 24.817 | 2.36× |
| MFCC | **1.992** | 7.517 | 4.379 | 2.20× |
| resample sinc 16→8 kHz | 0.649 | **0.569** | 1.339 | 0.88× |
| resample sinc 16→24 kHz | 1.748 | 1.627 | **1.267** | 0.72× |
| μ-law encode | **0.458** | 4.425 | 0.607 | 1.32× |
| time stretch 1.5× | **3.331** | 32.483 | 17.955 | 5.39× |

\* Save timings include the disk write and were noisy (Python per-run means 5.8–13.8 ms,
Neve 1.61–2.80 ms): read this ratio as "about 4–7×".

Correctness: spectrogram 133–134 dB, mel 116–122 dB and MFCC 119 dB SNR against the references;
resample 16→8 kHz 44.7–45.9 dB and 16→24 kHz 40.6–41.5 dB (different filters); μ-law decoded
difference ≤ 0.038; loads bit-exact against `soundfile`; time stretch 52.0 dB SNR against torchaudio.

---
## Limitations

- Peak RSS of the Neve process is ~3.2 GB (librosa 250–370 MB, torchaudio 298–358 MB):
  the runtime never frees `tensor.data`.
- Resampling is a fixed 64-tap sinc; torchaudio's default uses fewer taps and librosa's
  `soxr_hq` is a different algorithm.
- Timings are from one host; the numbers are not portable across machines.
