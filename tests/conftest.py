"""
tests/conftest.py

pytest imports this before any test module, so the auth environment is fixed
BEFORE backend.auth captures SECRET_KEY at import time. This removes an
import-order fragility: backend.auth reads SECRET_KEY once at import, so two
test modules declaring different secrets could otherwise make JWT signature
checks pass or fail depending on collection order.
"""

import os

os.environ.setdefault("OIL_USER_DB",      "file::memory:?cache=shared")
os.environ.setdefault("OIL_SECRET_KEY",   "test-secret-key-do-not-use-in-prod")
os.environ.setdefault("OIL_TOKEN_TTL",    "3600")
os.environ.setdefault("OIL_MAX_ATTEMPTS", "5")
os.environ.setdefault("OIL_LOCKOUT_SEC",  "900")
