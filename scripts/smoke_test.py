"""
scripts/smoke_test.py — v0.6.0
Fires HTTP requests against a running API server.
Called by api_smoke_test CI job after uvicorn starts.
"""

import httpx
import sys
import time

BASE = "http://localhost:8000"

TESTS = [
    ("GET", "/health",                           200),
    ("GET", "/",                                 200),
    ("GET", "/intelligence/graph/summary",       200),
    ("GET", "/intelligence/graph/edges",         200),
    ("GET", "/intelligence/entities",            200),
    ("GET", "/intelligence/entities/ids",        200),
    ("GET", "/intelligence/analyze/TA-001",      200),
    ("GET", "/intelligence/analyze/FAKE-0000",   404),
]

# Wait for server to be ready (CI race condition mitigation)
for attempt in range(10):
    try:
        httpx.get(f"{BASE}/health", timeout=2)
        break
    except Exception:
        print(f"  Waiting for server... attempt {attempt + 1}/10")
        time.sleep(1)

failed = []
for method, path, expected in TESTS:
    try:
        r = httpx.get(BASE + path, timeout=10)
        status = "PASS" if r.status_code == expected else "FAIL"
        print(f"  {status}: {method} {path} → {r.status_code} (expected {expected})")
        if status == "FAIL":
            failed.append(f"{path}: got {r.status_code}, expected {expected}")
    except Exception as e:
        print(f"  ERROR: {path} — {e}")
        failed.append(f"{path}: {e}")

print()
if failed:
    print(f"FAILED ({len(failed)} of {len(TESTS)}):")
    for f in failed:
        print(f"  - {f}")
    sys.exit(1)
else:
    print(f"All {len(TESTS)} smoke tests passed.")
    sys.exit(0)
