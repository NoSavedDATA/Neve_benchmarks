"""Run the four implementations, reject incorrect results, retain every sample."""
import argparse
import csv
import hashlib
import json
import os
import platform
import random
import re
import sqlite3
import statistics
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LANGUAGES = ["Neve", "Python", "C++", "C"]
MODES = ["memory", "file"]
SPEC = json.loads((ROOT / "spec.json").read_text())


def expected_results(n, queries):
    expected = {"insert_count": n, "insert_quantity": sum(i % 50 for i in range(n)),
                "update_quantity": sum(i % 50 + 1 for i in range(n)), "update_exact": n, "delete_count": 0}
    for case in SPEC["queries"]:
        rows = ids = quantities = 0
        for iteration in range(queries):
            for item_id in range(n):
                customer = item_id % 100
                quantity = item_id % 50
                kind = case["kind"]
                if kind == 0:
                    keep = item_id == iteration % n and (not case["join"] or customer % 2 == 0)
                elif kind == 1:
                    keep = customer == iteration % 100 and quantity >= 25
                elif kind == 2:
                    low = iteration % 10 * 5
                    keep = low <= quantity < low + 5
                elif kind == 3:
                    keep = customer == iteration % 100 and customer % 10 == iteration % 10 and quantity >= 25
                else:
                    keep = (quantity + customer % 10) % 10 == iteration % 10
                if keep:
                    rows += 1
                    ids += item_id
                    quantities += quantity
        expected[case["name"] + "_rows"] = rows
        expected[case["name"] + "_ids"] = ids
        expected[case["name"] + "_quantity"] = quantities
    return expected


def parameters(kind, i, n):
    if kind == 0: return (i % n,)
    if kind == 1: return (i % 100, 25)
    if kind == 2: return (i % 10 * 5, i % 10 * 5 + 5)
    if kind == 3: return (i % 100, i % 10, 25)
    return (i % 10,)


def reference_and_plans(n, queries, expected):
    db = sqlite3.connect(":memory:")
    db.executescript(SPEC["schema"])
    db.executemany("INSERT INTO customers VALUES (?, ?, ?)", [(i, i % 10, i % 2 == 0) for i in range(100)])
    db.executemany("INSERT INTO items VALUES (?, ?, ?, ?, ?)", [(i, i % 100, i % 50, 42.5, SPEC["payload"]) for i in range(n)])
    plans = {}
    for case in SPEC["queries"]:
        count = ids = quantity = 0
        for i in range(queries):
            for row in db.execute(case["sql"], parameters(case["kind"], i, n)):
                count += 1; ids += row[0]; quantity += row[1]
                assert row[2] == 42.5 and row[3] == SPEC["payload"]
        assert count == expected[case["name"] + "_rows"]
        assert ids == expected[case["name"] + "_ids"]
        assert quantity == expected[case["name"] + "_quantity"]
        plans[case["name"]] = [list(row) for row in db.execute("EXPLAIN QUERY PLAN " + case["sql"], parameters(case["kind"], 0, n))]
    db.close()
    return plans


def command(language):
    return {"Neve": ["/root/.local/neve/bin/neve", str(ROOT / "workload.nv")],
            "Python": [sys.executable, str(ROOT / "workload.py")],
            "C++": [str(Path("/opt/neve-benchmark-bin/benchmark-cpp"))], "C": [str(Path("/opt/neve-benchmark-bin/benchmark-c"))]}[language]


def output(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return p.stdout.strip()


def quantile(values, fraction):
    values = sorted(values)
    position = (len(values) - 1) * fraction
    low = int(position); high = min(low + 1, len(values) - 1)
    return values[low] + (values[high] - values[low]) * (position - low)


def summarize(records):
    groups = {}
    for record in records:
        if not record["warmup"]:
            for metric, value in record["metrics_us"].items():
                groups.setdefault((record["mode"], record["language"], metric), []).append(value / 1000)
    rows = []
    for (mode, language, metric), values in groups.items():
        rows.append(dict(mode=mode, language=language, metric=metric, runs=len(values),
                         median_ms=statistics.median(values), q1_ms=quantile(values, .25), q3_ms=quantile(values, .75),
                         min_ms=min(values), max_ms=max(values), mean_ms=statistics.mean(values),
                         stdev_ms=statistics.stdev(values) if len(values) > 1 else 0))
    return sorted(rows, key=lambda r: (MODES.index(r["mode"]), r["metric"], LANGUAGES.index(r["language"])))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repetitions", type=int, default=15)
    parser.add_argument("--warmups", type=int, default=2)
    parser.add_argument("--rows", type=int, default=1000)
    parser.add_argument("--queries", type=int, default=1000)
    parser.add_argument("--modes", default="memory,file")
    parser.add_argument("--output", type=Path, default=Path("/results"))
    args = parser.parse_args()
    modes = args.modes.split(",")
    if args.repetitions < 1 or args.warmups < 0 or not (1 <= args.rows <= 1000) or not (1 <= args.queries <= 1000):
        parser.error("Counts must be positive; rows and queries are limited to 1000 for the verified integer checksums")
    if len(modes) != len(set(modes)) or any(mode not in MODES for mode in modes):
        parser.error("Unknown or duplicated storage mode")
    args.output.mkdir(parents=True, exist_ok=True)
    expected = expected_results(args.rows, args.queries)
    plans = reference_and_plans(args.rows, args.queries, expected)
    cpu = min(os.sched_getaffinity(0))
    cpu_info = Path("/proc/cpuinfo").read_text()
    sources = [p for p in ROOT.rglob("*") if p.is_file() and p.suffix in {".c", ".cpp", ".h", ".nv", ".py", ".json", ".sh"} and "results" not in p.parts and "smoke-results" not in p.parts and "build" not in p.parts]
    library_files = [Path("/root/.local/neve/lib/db/lib.so"), Path("/root/.local/neve/lib/batchbench/lib.so"), Path("/root/.local/neve/bin/neve")]
    import _sqlite3
    metadata = dict(utc_started=datetime.now(timezone.utc).isoformat(), timezone="America/Sao_Paulo", rows=args.rows,
                    queries_per_case=args.queries, repetitions=args.repetitions, warmups=args.warmups, modes=modes,
                    language_order=LANGUAGES, cpu_affinity=[cpu], logical_cpus=os.cpu_count(), platform=platform.platform(),
                    cpu_model=next(line.split(":", 1)[1].strip() for line in cpu_info.splitlines() if line.startswith("model name")),
                    python=sys.version, sqlite=sqlite3.sqlite_version, clang=output(["clang-21", "--version"]).splitlines()[0],
                    c_flags="-std=c11 -O3 -DNDEBUG -Wall -Wextra", cpp_flags="-std=c++17 -O3 -DNDEBUG -Wall -Wextra",
                    order_seed=42, spec=SPEC, expected=expected, query_plans=plans,
                    source_hashes={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
                    runtime_hashes={str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in library_files},
                    sqlite_linkage={"Python": output(["ldd", _sqlite3.__file__]),
                                    "Neve": output(["ldd", "/root/.local/neve/lib/db/lib.so"]),
                                    "C++": output(["ldd", str(Path("/opt/neve-benchmark-bin/benchmark-cpp"))]),
                                    "C": output(["ldd", str(Path("/opt/neve-benchmark-bin/benchmark-c"))])},
                    filesystem=output(["stat", "-f", "-c", "%T", "/tmp"]),
                    storage={"memory": {"journal_mode": "MEMORY", "synchronous": "OFF"},
                             "file": {"journal_mode": "WAL", "synchronous": "FULL", "location": "/tmp, new file per sample"}},
                    sql_cache_size_kib=4096, python_statement_cache=128, prepared_statement_reuse=True,
                    batch_semantics="1000 individual parameterized statements in one transaction per write phase")
    required = {name + "_us" for name in ["insert", "update", "delete", "work"] + [q["name"] for q in SPEC["queries"]]}
    env = os.environ.copy()
    env.update(NEVE_LIBS="/root/.local/neve/lib", BENCH_N=str(args.rows), BENCH_QUERIES=str(args.queries))
    jobs = [(mode, language) for mode in modes for language in LANGUAGES]
    rng = random.Random(42)
    records = []
    failures = []
    total = (args.repetitions + args.warmups) * len(jobs)
    with tempfile.TemporaryDirectory(prefix="neve-batch-benchmark-", dir="/tmp") as temp:
        for round_number in range(args.warmups + args.repetitions):
            order = jobs.copy(); rng.shuffle(order)
            for mode, language in order:
                sample_id = len(records) + len(failures) + 1
                path = ":memory:" if mode == "memory" else str(Path(temp) / f"sample-{sample_id}.sqlite3")
                env["BENCH_DATABASE"] = path
                began = time.perf_counter_ns()
                p = subprocess.run(command(language), cwd=ROOT, env=env, text=True, capture_output=True, timeout=180,
                                   preexec_fn=lambda: os.sched_setaffinity(0, {cpu}))
                elapsed_us = (time.perf_counter_ns() - began) // 1000
                metric_pairs = re.findall(r"^METRIC\s+(\w+)\s+(\d+)\s*$", p.stdout, re.MULTILINE)
                check_pairs = re.findall(r"^CHECK\s+(\w+)\s+(\d+)\s*$", p.stdout, re.MULTILINE)
                metrics = {k: int(v) for k, v in metric_pairs}
                checks = {k: int(v) for k, v in check_pairs}
                valid = (p.returncode == 0 and checks == expected and set(metrics) == required
                         and len(metric_pairs) == len(metrics) and len(check_pairs) == len(checks)
                         and metrics["work_us"] == sum(v for k, v in metrics.items() if k != "work_us"))
                metrics["process_us"] = elapsed_us
                record = dict(mode=mode, language=language, sample_id=sample_id,
                              warmup=round_number < args.warmups, repetition=max(0, round_number - args.warmups + 1),
                              metrics_us=metrics, checks=checks, valid=valid, exit_code=p.returncode,
                              command=command(language), stdout=p.stdout, stderr=p.stderr)
                if not valid:
                    failures.append(record)
                    (args.output / "failure.json").write_text(json.dumps(dict(metadata=metadata, records=records, failures=failures), indent=2))
                    raise RuntimeError("Sample failed: " + json.dumps(record))
                records.append(record)
                (args.output / "raw.json").write_text(json.dumps(dict(metadata=metadata, records=records, failures=failures), indent=2))
                print(f"[{sample_id}/{total}] {'warmup' if record['warmup'] else 'run ' + str(record['repetition'])} {language:6} {mode:6} | trabalho {metrics['work_us']/1000:.3f} ms | processo {elapsed_us/1000:.1f} ms | validado", flush=True)
    metadata["utc_finished"] = datetime.now(timezone.utc).isoformat()
    (args.output / "raw.json").write_text(json.dumps(dict(metadata=metadata, records=records, failures=failures), indent=2))
    rows = summarize(records)
    with (args.output / "summary.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    flat = [dict(mode=r["mode"], language=r["language"], sample_id=r["sample_id"], warmup=r["warmup"],
                 repetition=r["repetition"], metric=k, elapsed_us=v, valid=r["valid"])
            for r in records for k, v in r["metrics_us"].items()]
    with (args.output / "raw.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(flat[0])); writer.writeheader(); writer.writerows(flat)
    print(f"COMPLETE: {len(records)} samples, {len(failures)} failures", flush=True)
    print("\nResumo: mediana por lote (ms); menor e melhor.")
    for mode in modes:
        print("\nArmazenamento:", mode)
        print("{:<22}".format("Etapa") + "".join("{:>12}".format(language) for language in LANGUAGES))
        for metric in ["insert_us", "update_us", "delete_us"] + [q["name"] + "_us" for q in SPEC["queries"]] + ["work_us", "process_us"]:
            values = [next(row["median_ms"] for row in rows if row["mode"] == mode and row["language"] == language and row["metric"] == metric) for language in LANGUAGES]
            print("{:<22}".format(metric) + "".join("{:>12.3f}".format(value) for value in values))



if __name__ == "__main__":
    main()
