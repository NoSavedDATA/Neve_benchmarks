# ESP32-S3 benchmark supplement

This supplement supports the embedded execution subsection. It contains
selected on-device measurements, a host-side verifier, and the source of
seven benchmark pairs for inspection. The study evaluated eight kernels.
The matrix multiplication timing rows are included as historical data and
its kernel source is excluded from this distribution.

## Recompute the timing results

From this directory, use Python 3.12 or newer with the standard library:

```sh
python -B data/verify_numeric_data.py
```

Expected output is `PASS` for 96 boot CSVs, 9,360 samples, 36 historical
aggregate rows, and eight experimental-policy rows. This command requires
no network, SDK, compiler, or microcontroller. `data/SAMPLES.json` maps
each CSV to its experiment, kernel, optimization, variant, and boot.
`data/INVENTORY.json` records the SHA-256 hashes of the included inputs.

## Method and interpretation

The historical measurements use a 240 MHz ESP32-S3 (revision v0.2), Xtensa
GCC 15.2.0 for C, host LLVM 20.1.8 and Espressif LLVM 20.1.1 for AnonLang,
and ESP-IDF v6.0.2. The ahead-of-time pipeline emits LLVM IR, lowers it
to windowed Xtensa objects, and links them into firmware. The embedded
subset executes without the full language runtime.

The historical series covers O0, O2, and Os. Each configuration has three
boots and 30 measured C/AnonLang pairs per scenario per boot after warm-up.
Execution order alternates between implementations. Timing windows measure
CCOUNT cycles and microseconds. Initialization, serial output, and numerical
checks are outside the kernel windows. The reported cycle ratio is the median
of the three ratios of within-boot median cycle counts (AnonLang divided by C).
The boot is the repetition unit. Ratios describe the two toolchains on this
target. The experiment did not test statistical significance.

`data/historical-performance.csv` supports the paper's O2 results. FIR,
IIR, and FFT used 1.12, 1.42, and 1.43 times the C cycles, respectively.
The O2 range was 0.93 (linear search, target at the end) to 2.65 (array sum).

`data/hwloop-policy.csv` compares two experimental variants of the AnonLang
backend at O2. Its denominator is the reference AnonLang backend. Treat
those 24 boots as a separate experiment from the 72 historical boots.

## Source and scope

`kernels/` provides the C and AnonLang kernel pairs and expected-value
metadata. This review copy omits the upstream compiler, firmware, build
integration, serial logs, and original provenance paths. The verifier
recomputes timing aggregates. It does not rebuild firmware, repeat on-device
measurements, or independently validate the original ELF or serial identity.

AnonLang is the review name for the language. The review copy substitutes
that name in implementation labels, aggregate column names, and source symbols.
The numerical measurements, row order, and benchmark algorithms are preserved.

## Notices

The timing data use CC BY 4.0. See `data/LICENSE-CC-BY-4.0.txt`. This review
copy uses anonymous attribution and records the label substitutions above.
The kernel and verifier source use the MIT terms in `LICENSE-MIT.txt` with
anonymous attribution for review.
