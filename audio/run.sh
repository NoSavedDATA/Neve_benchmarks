#!/usr/bin/env bash
# Full benchmark: test signals, librosa/torchaudio (1 thread and default threads), Neve, merge.
# NEVE_AUDIO_BENCH_RUNS (default 3): repetitions of every implementation; merge.py reports medians.
# NEVE_AUDIO_BENCH_RESULTS: output directory (default results/ next to this script).
set -euo pipefail

HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"
RUNS=${NEVE_AUDIO_BENCH_RUNS:-3}

echo "== [1/5] setup: test signals =="
bash setup.sh

OUT=${NEVE_AUDIO_BENCH_RESULTS:-$HERE/results}
export NEVE_AUDIO_BENCH_RESULTS="$OUT"
mkdir -p "$OUT"
rm -rf "$OUT"/* "$OUT"/.[!.]* 2>/dev/null || true
# bench_neve.nv writes to results/ (relative path): point it at the chosen directory.
if [ "$OUT" != "$HERE/results" ]; then
  rm -rf "$HERE/results"
  ln -s "$OUT" "$HERE/results"
fi

# 1T columns run pinned to one core (the first one this container may use); defT runs are not pinned.
PIN=""
if command -v taskset >/dev/null 2>&1; then
  CPU=$(taskset -pc $$ | sed 's/.*: //; s/[,-].*//')
  PIN="taskset -c $CPU"
fi
ONE="env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1"
RSS="python3 $HERE/run_with_rss.py"

for r in $(seq 1 "$RUNS"); do
  echo "== [2/5] python: librosa / torchaudio (1 thread), run $r/$RUNS =="
  $RSS librosa 1T "$r" -- $PIN $ONE python3 bench_py.py --impl librosa --threads 1 > "$OUT/librosa_1_r$r.csv"
  $RSS torchaudio 1T "$r" -- $PIN $ONE python3 bench_py.py --impl torchaudio --threads 1 > "$OUT/torchaudio_1_r$r.csv"

  echo "== [3/5] python: librosa / torchaudio (default threads), run $r/$RUNS =="
  $RSS librosa defT "$r" -- python3 bench_py.py --impl librosa --threads default > "$OUT/librosa_default_r$r.csv"
  $RSS torchaudio defT "$r" -- python3 bench_py.py --impl torchaudio --threads default > "$OUT/torchaudio_default_r$r.csv"

  echo "== [4/5] neve, run $r/$RUNS =="
  $RSS neve 1T "$r" -- $PIN neve bench_neve.nv > "$OUT/neve_r$r.csv"
done

echo "== [5/5] merge + correctness cross-check =="
python3 merge.py

echo "== done =="
