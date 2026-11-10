# Database dataset benchmark: Neve, Python, C++ and C

This CPU-only experiment compares the four language interfaces to the same
system SQLite engine. Neve uses `db`, Python uses the standard-library `sqlite3`
module, C++ uses RAII wrappers around sqlite3, and C uses the native sqlite3 API.

## Run with Docker

Requirements: Docker with Compose v2, Linux containers, internet during the first
build, and an x86-64 host. This experiment does not require a GPU or CUDA.
Following the same folder-local workflow as `net/`, build from this directory:

```bash
git clone https://github.com/NoSavedDATA/Neve_benchmarks.git
cd Neve_benchmarks/datasets
docker build --platform linux/amd64 -t neve_datasets .
docker run --rm -it -v "$(pwd)/resultados:/results" neve_datasets bash
```

Inside the container, run a quick correctness check across all four languages:

```bash
python3 run.py --repetitions 1 --warmups 0
```

Then run the full experiment:

```bash
python3 run.py
```

To inspect a single implementation inside the container:

```bash
neve workload.nv
python3 workload.py
/opt/neve-benchmark-bin/benchmark-cpp
/opt/neve-benchmark-bin/benchmark-c
```

These individual programs use in-memory databases by default. Use the runner
for automatic validation, repeated samples and both storage modes.

As a non-interactive alternative, Docker Compose runs the same benchmark:

```bash
docker compose build
docker compose run --rm benchmark --repetitions 1 --warmups 0
docker compose run --rm benchmark
```

Default: 15 measured samples and two discarded warmups for each of four languages
and two storage modes: 120 measured samples and 16 warmups. Each sample starts a
new process and a fresh database. Correctness failures stop the experiment.

Results persist on the host under `datasets/resultados/`:

- `summary.csv`: median, quartiles, minimum, maximum, mean and standard deviation.
- `raw.csv`: individual timings, including identified warmups.
- `raw.json`: commands, outputs, result checks, source/runtime hashes and query plans.

The runner also prints summary tables at completion. Failed samples are retained
in `failure.json`; no timing outliers are discarded.

## Workload

Each sample creates 100 reference customers outside the phase timers and then:

1. Inserts 1,000 items containing integer, text and REAL fields.
2. Runs each of the six SELECT cases 1,000 times.
3. Updates all 1,000 items, changing integer, text and REAL fields.
4. Deletes all 1,000 items, leaving zero item rows.

Each write phase has one transaction containing 1,000 individual parameterized
statements. It is not a single multi-row INSERT or 1,000 separate commits.
Statements are reused through SQLite reset or Python's statement cache.
Every write checks that exactly one row was affected.

| SELECT case | Rows consumed across 1,000 executions |
| --- | ---: |
| Primary-key lookup with WHERE | 1,000 |
| Indexed WHERE on customer and quantity | 5,000 |
| Scan-based WHERE on a quantity range | 100,000 |
| INNER JOIN with WHERE on ID and active customer | 500 |
| INNER JOIN with indexed WHERE on customer, region and quantity | 5,000 |
| INNER JOIN with an arithmetic WHERE predicate | 100,000 |

All rows are consumed and materialized; integer, text and REAL values are checked.
JOINs also check the related customer's region. Aggregate counts and checksums
are compared to independent Python predicates and a SQLite reference before the
timed samples. REAL values 42.5 and 99.5 are exact in both float32 and float64.
The SQL schema and queries are in `spec.json` and `queries.h`.

## Timings and storage

Internal timers include statement preparation, loops, parameter binding, row
consumption, local validation and statement finalization. Write timers include
BEGIN and COMMIT. Schema setup and aggregate validation are outside phase timers.
`work_us` is the sum of the nine phase timings for each sample.

`process_us` measures the whole child process externally. It includes startup,
database setup, aggregate checks, output and shutdown, plus Neve compilation/JIT.
C and C++ are compiled before measurement; their compilation is excluded.
All measurements are monotonic-clock microseconds; summary tables use milliseconds.

- Memory: `:memory:`, journal_mode=MEMORY, synchronous=OFF.
- File: a new temporary file per sample, journal_mode=WAL, synchronous=FULL.
- Both: foreign_keys=ON, temp_store=MEMORY, cache_size=-4096 KiB, busy_timeout=5000 ms.
- Runs are sequential and pinned to one allowed logical CPU, in randomized order
  with seed 42. Warmups affect system caches; they do not keep the JIT alive.
- Temporary database files are removed after the run. Personal databases are unused.

The file experiment uses the container filesystem and warm caches; it is not a
cold-disk or concurrency benchmark. Shared SQLite execution, language interfaces,
string allocation and validation costs all contribute to the observed times.

## Dependencies and package layout

The Dockerfile installs `libsqlite3-dev` explicitly and obtains the SQLite library
with `nsm i danielcasanova12/db`. The native `lib.so` is downloaded from that
repository's release tagged `latest`. SQLite library sources are maintained there.

The small `support/` helper supplies only a monotonic clock, environment settings
and assertion helpers. `setup.sh` compiles it into the Neve library directory as
`batchbench`; loops and database operations remain in `workload.nv`.
C and C++ are compiled with Clang 21 and `-O3`.

The current SQLite binary targets Ubuntu 22.04 amd64 and Neve linked against
LLVM 21. Rebuild the library if the upstream rolling Neve installer changes ABI.
`raw.json` records executable/library hashes and linkage for each benchmark run.

## Reference measurements

The following are historical measurements from 2026-10-20, on an Intel Core
i5-9400F at 2.90 GHz, Python 3.10.12, SQLite 3.37.2 and Clang 21.1.8. Each value
is the median of 15 runs of the complete nine-phase workload, excluding process
initialization and JIT. The original numeric summary is `reference-results.csv`.

| Language | In-memory (ms) | File WAL/FULL (ms) |
| --- | ---: | ---: |
| Neve | 244.543 | 269.330 |
| Python | 410.196 | 429.106 |
| C++ | 222.095 | 241.985 |
| C | 216.803 | 239.109 |

Historical full-process medians were 2664.213/2721.120 ms for Neve,
466.116/500.944 ms for Python, 234.209/270.015 ms for C++, and
225.019/265.441 ms for C (memory/file). Internal performance and process startup
should be considered separately. New hardware, runtimes and libraries may differ.


---
# ORM model

Visit the [orm repository](https://github.com/danielcasanova12/orm) for a high-level database library, i.e, an Object-Relational Mapping based library.
