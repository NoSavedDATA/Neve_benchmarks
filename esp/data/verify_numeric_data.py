"""Verify selected CSV integrity and reproduce timing aggregates, without firmware/toolchains."""
import csv
import hashlib
import io
import json
from pathlib import Path
from statistics import median
import sys

def close(a, b):
    assert abs(float(a) - float(b)) <= 1e-8 * max(1, abs(float(b))), (a, b)

def verify(root):
    inventory = json.loads((root / 'INVENTORY.json').read_text(encoding='utf-8'))
    actual = {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()
              and '__pycache__' not in p.parts}
    assert actual == set(inventory) | {'INVENTORY.json'}, 'Inventory membership mismatch'
    for name, expected in inventory.items():
        p = root / name
        assert not p.is_symlink() and p.resolve().is_relative_to(root.resolve())
        assert hashlib.sha256(p.read_bytes()).hexdigest() == expected, name
    entries = json.loads((root / 'SAMPLES.json').read_text(encoding='utf-8'))
    groups = {}
    samples = 0
    for entry in entries:
        rows = list(csv.DictReader(io.StringIO((root / entry['file']).read_text(encoding='utf-8-sig'))))
        assert rows and all(r['status'] == 'OK' and not r['error'] for r in rows)
        assert all(int(r['boot']) == int(entry['boot']) for r in rows)
        samples += len(rows)
        scenarios = {r['scenario'] or 'default' for r in rows}
        for scenario in scenarios:
            selected = [r for r in rows if (r['scenario'] or 'default') == scenario]
            assert len(selected) == 60
            pairs = {}
            medians = {}
            for row in selected:
                key = int(row['repetition'])
                assert row['impl'] in ('c', 'anonlang') and int(row['cycles']) >= 0 and int(row['time_us']) >= 0
                assert row['impl'] not in pairs.setdefault(key, set())
                pairs[key].add(row['impl'])
            assert len(pairs) == 30 and all(v == {'c', 'anonlang'} for v in pairs.values())
            for impl in ('c', 'anonlang'):
                medians[impl] = {metric: median(float(r[metric]) for r in selected if r['impl'] == impl)
                                 for metric in ('cycles', 'time_us')}
            key = (entry['set'], entry['benchmark'], entry['optimization'], scenario, entry['variant'])
            groups.setdefault(key, []).append((entry['boot'], medians))
    def group(set_name, benchmark, opt, scenario, variant):
        boots = groups[(set_name, benchmark, opt, scenario, variant)]
        assert sorted(b for b, _ in boots) == [1, 2, 3]
        return [m for _, m in sorted(boots)]
    historical = list(csv.DictReader((root / 'historical-performance.csv').open(encoding='utf-8-sig')))
    for row in historical:
        boots = group('historical', row['benchmark'], row['optimization'], row['scenario'], 'historical')
        for impl in ('c', 'anonlang'):
            close(median(m[impl]['cycles'] for m in boots), row[impl+'_cycles_median'])
            close(median(m[impl]['time_us'] for m in boots), row[impl+'_time_median'])
        close(median(m['anonlang']['cycles']/m['c']['cycles'] for m in boots), row['ratio_cycles'])
    policy = list(csv.DictReader((root / 'hwloop-policy.csv').open(encoding='utf-8-sig')))
    for row in policy:
        aggregate = {}
        for variant in ('reference', 'candidate'):
            boots = group('policy', row['benchmark'], 'O2', row['scenario'], variant)
            aggregate[variant] = median(m['anonlang']['cycles'] for m in boots)
            close(aggregate[variant], row[variant+'_cycles'])
            close(median(m['anonlang']['time_us'] for m in boots), row[variant+'_us'])
        close(100*(aggregate['candidate']/aggregate['reference']-1), row['change_percent'])
    assert len(entries) == 96 and samples == 9360 and len(historical)==36 and len(policy)==8
    return {'status': 'PASS', 'csv_boots': len(entries), 'samples': samples,
            'historical_rows_reproduced': len(historical), 'policy_rows_reproduced': len(policy),
            'scope': 'Timing aggregate reproduction; does not independently establish ELF/serial validity, oracle correctness, static size or memory attribution'}

if __name__ == '__main__':
    print(json.dumps(verify(Path(__file__).resolve().parent), indent=2))
