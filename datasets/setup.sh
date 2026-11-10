#!/usr/bin/env bash
set -euo pipefail
PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
export NEVE_LIBS="${NEVE_LIBS:-$HOME/.local/neve/lib}"
test -s "$NEVE_LIBS/db/lib.so"
mkdir -p "$NEVE_LIBS/batchbench/src/codegen" /opt/neve-benchmark-bin /results
cp "$PROJECT_DIR/support/Makefile" "$PROJECT_DIR/support/include.nv" "$NEVE_LIBS/batchbench/"
cp "$PROJECT_DIR/support/src/include.h" "$PROJECT_DIR/support/src/runtime.cpp" "$NEVE_LIBS/batchbench/src/"
cp "$PROJECT_DIR/support/src/codegen/path.cpp" "$NEVE_LIBS/batchbench/src/codegen/"
make -B -C "$NEVE_LIBS/batchbench" -j2 NEVE_ROOT="$(cd "$NEVE_LIBS/.." && pwd)"
clang-21 -std=c11 -O3 -DNDEBUG -Wall -Wextra "$PROJECT_DIR/workload.c" -lsqlite3 -o /opt/neve-benchmark-bin/benchmark-c
clang++-21 -std=c++17 -O3 -DNDEBUG -Wall -Wextra "$PROJECT_DIR/workload.cpp" -lsqlite3 -o /opt/neve-benchmark-bin/benchmark-cpp
