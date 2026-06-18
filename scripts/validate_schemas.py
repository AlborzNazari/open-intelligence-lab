"""
scripts/validate_schemas.py — v0.6.0
Validates all dataset JSON files. Called by schema_validate CI job.
Paths are resolved relative to the project root, not the script location.
"""

import json
import pathlib
import sys

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent

DATASETS = [
    PROJECT_ROOT / "datasets" / "threat_entities.json",
    PROJECT_ROOT / "datasets" / "attack_patterns.json",
    PROJECT_ROOT / "datasets" / "relations.json",
    PROJECT_ROOT / "datasets" / "campaigns.json",
    PROJECT_ROOT / "datasets" / "mitre_mapping.json",
]

errors = []
for path in DATASETS:
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(data, list):
                raise ValueError(f"Expected a JSON array, got {type(data).__name__}")
            print(f"  OK: {path.name} ({len(data)} entries)")
        except Exception as e:
            errors.append(f"{path.name}: {e}")
            print(f"  FAIL: {path.name} — {e}")
    else:
        print(f"  MISSING: {path} — file not found")
        errors.append(f"{path.name}: file not found")

if errors:
    print(f"\n{len(errors)} error(s) found.")
    sys.exit(1)
else:
    print(f"\nAll {len(DATASETS)} dataset files valid.")
    sys.exit(0)
