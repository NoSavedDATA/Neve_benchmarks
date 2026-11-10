import json
import os
import sqlite3
import time
from pathlib import Path

spec = json.loads(Path(__file__).with_name("spec.json").read_text())
n = int(os.environ.get("BENCH_N", "1000"))
query_count = int(os.environ.get("BENCH_QUERIES", "1000"))
path = os.environ.get("BENCH_DATABASE", ":memory:")
db = sqlite3.connect(path, isolation_level=None, cached_statements=128)
db.execute("PRAGMA busy_timeout=5000")
if path == ":memory:":
    db.executescript("PRAGMA journal_mode=MEMORY; PRAGMA synchronous=OFF;")
else:
    db.executescript("PRAGMA journal_mode=WAL; PRAGMA synchronous=FULL;")
db.executescript(spec["schema"])
db.execute("BEGIN")
for i in range(100):
    db.execute("INSERT INTO customers VALUES (?, ?, ?)", (i, i % 10, int(i % 2 == 0)))
db.execute("COMMIT")
cursor = db.cursor()
metrics = {}
checks = {}

def scalar(sql):
    return db.execute(sql).fetchone()[0]

def parameters(kind, iteration):
    if kind == 0:
        return (iteration % n,)
    if kind == 1:
        return (iteration % 100, 25)
    if kind == 2:
        low = iteration % 10 * 5
        return (low, low + 5)
    if kind == 3:
        return (iteration % 100, iteration % 10, 25)
    return (iteration % 10,)

start = time.perf_counter_ns()
db.execute("BEGIN")
for i in range(n):
    cursor.execute("INSERT INTO items (id, customer_id, quantity, price, label) VALUES (?, ?, ?, ?, ?)",
                   (i, i % 100, i % 50, 42.5, spec["payload"]))
    if cursor.rowcount != 1:
        raise RuntimeError("INSERT rowcount")
db.execute("COMMIT")
metrics["insert_us"] = (time.perf_counter_ns() - start) // 1000
checks["insert_count"] = scalar("SELECT COUNT(*) FROM items")
checks["insert_quantity"] = scalar("SELECT SUM(quantity) FROM items")

for query in spec["queries"]:
    count = id_sum = quantity_sum = 0
    start = time.perf_counter_ns()
    for i in range(query_count):
        cursor.execute(query["sql"], parameters(query["kind"], i))
        for row in cursor:
            count += 1
            id_sum += row[0]
            quantity_sum += row[1]
            if row[2] != 42.5 or row[3] != spec["payload"]:
                raise RuntimeError("REAL/TEXT mismatch")
            if query["join"] and row[4] != row[0] % 10:
                raise RuntimeError("JOIN mismatch")
    metrics[query["name"] + "_us"] = (time.perf_counter_ns() - start) // 1000
    checks[query["name"] + "_rows"] = count
    checks[query["name"] + "_ids"] = id_sum
    checks[query["name"] + "_quantity"] = quantity_sum

start = time.perf_counter_ns()
db.execute("BEGIN")
for i in range(n):
    cursor.execute("UPDATE items SET quantity = ?, price = ?, label = ? WHERE id = ?",
                   (i % 50 + 1, 99.5, spec["updated_payload"], i))
    if cursor.rowcount != 1:
        raise RuntimeError("UPDATE rowcount")
db.execute("COMMIT")
metrics["update_us"] = (time.perf_counter_ns() - start) // 1000
checks["update_quantity"] = scalar("SELECT SUM(quantity) FROM items")
checks["update_exact"] = scalar("SELECT COUNT(*) FROM items WHERE quantity = (id % 50) + 1 AND price = 99.5 AND label = 'benchmark-updated-payload'")

start = time.perf_counter_ns()
db.execute("BEGIN")
for i in range(n):
    cursor.execute("DELETE FROM items WHERE id = ?", (i,))
    if cursor.rowcount != 1:
        raise RuntimeError("DELETE rowcount")
db.execute("COMMIT")
metrics["delete_us"] = (time.perf_counter_ns() - start) // 1000
checks["delete_count"] = scalar("SELECT COUNT(*) FROM items")
cursor.close()
db.close()
metrics["work_us"] = sum(metrics.values())
for name, value in metrics.items():
    print("METRIC", name, value)
for name, value in checks.items():
    print("CHECK", name, value)
