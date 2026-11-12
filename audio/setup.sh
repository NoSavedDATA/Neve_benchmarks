#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname -- "${BASH_SOURCE[0]}")"
export NEVE_LIBS="${NEVE_LIBS:-$HOME/.local/neve/lib}"

# The audio lib must be installed first: nsm i freds0/audio
test -s "$NEVE_LIBS/audio/lib.so"

echo "Generating test signals..."
python3 gen_data.py
mkdir -p results

echo "----------------------------------------"
echo "Setup complete! You can now run the benchmark:"
echo "neve bench_neve.nv > results/neve.csv"
