import httpx
import sys

base = 'http://localhost:8000'
tests = [
    ('GET', '/health', 200),
    ('GET', '/intelligence/graph/summary', 200),
    ('GET', '/intelligence/entities', 200),
]

failed = []
for method, path, expected in tests:
    try:
        r = httpx.get(base + path, timeout=5)
        status = 'PASS' if r.status_code == expected else 'FAIL'
        print(f"  {status}: {method} {path} -> {r.status_code}")
        if status == 'FAIL':
            failed.append(path)
    except Exception as e:
        print(f"  ERROR: {path} - {e}")
        failed.append(path)

sys.exit(1 if failed else 0)
