import json
import pathlib
import sys

datasets = [
    'data/entities.json',
    'data/attack_patterns.json',
    'data/relations.json',
    'data/campaigns.json'
]

errors = []
for d in datasets:
    p = pathlib.Path(d)
    if p.exists():
        try:
            json.loads(p.read_text())
            print(f"  OK: {d}")
        except Exception as e:
            errors.append(f"{d}: {e}")
            print(f"  FAIL: {d} - {e}")
    else:
        print(f"  SKIP: {d} (not found)")

sys.exit(1 if errors else 0)
