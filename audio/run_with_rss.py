#!/usr/bin/env python3
"""Run a command and record its peak resident memory.

Usage: run_with_rss.py <impl> <threads> <run> -- <command...>
The command's stdout/stderr pass through untouched (callers redirect stdout into a CSV);
one line "<impl>,<threads>,<run>,<peak_rss_mb>" is appended to $NEVE_AUDIO_BENCH_RESULTS/rss.csv
(default: results/ next to this file). The peak covers the whole process, i.e. also the Python
interpreter and its libraries, or the Neve compiler/JIT: compare orders of magnitude, not megabytes.
"""
import os
import resource
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.environ.get("NEVE_AUDIO_BENCH_RESULTS", os.path.join(HERE, "results"))


def main():
    if "--" not in sys.argv:
        sys.exit(__doc__)
    cut = sys.argv.index("--")
    impl, threads, run = sys.argv[1:cut]
    rc = subprocess.call(sys.argv[cut + 1:])
    mb = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss / 1024.0   # KiB on Linux
    os.makedirs(RES, exist_ok=True)
    with open(os.path.join(RES, "rss.csv"), "a") as f:
        if f.tell() == 0:
            f.write("impl,threads,run,peak_rss_mb\n")
        f.write(f"{impl},{threads},{run},{mb:.1f}\n")
    sys.exit(rc)


if __name__ == "__main__":
    main()
