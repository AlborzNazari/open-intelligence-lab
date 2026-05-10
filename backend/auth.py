"""
OIL v0.7 — User Authentication & Authorization
JWT-based auth with role enforcement (analyst / admin).
Uses SQLite for the user store (zero external deps beyond what's already in the stack).
"""

import os
import sqlite3
import hashlib
import hmac
import secrets
import time
import base64
import json
import threading
from typing import Optional

from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# ── Config ────────────────────────────────────────────────────────────────────

SECRET_KEY: str = os.getenv("OIL_SECRET_KEY", secrets.token_hex(32))
TOKEN_TTL_SECONDS: int = int(os.getenv("OIL_TOKEN_TTL", 3600))   # 1 h default
DB_PATH: str = os.getenv("OIL_USER_DB", "oil_users.db")

ROLES = {"analyst", "admin"}

# ── Database bootstrap ────────────────────────────────────────────────────────

# Singleton connection for in-memory databases (":memory:" or "file::memory:...").
# SQLite in-memory databases are destroyed when their last connection closes.
# For production file-based databases we create a new connection per call, which
# is correct. For in-memory (test) databases we hold one persistent connection
# for the process lifetime so the database survives across calls.
_mem_conn: Optional[sqlite3.Connection] = None
_mem_lock = threading.Lock()


def get_db() -> sqlite3.Connection:
    """
    Return a SQLite connection appropriate for DB_PATH.

    File paths  → new connection per call (standard SQLite usage).
    Memory paths → singleton connection held for the process lifetime so the
                   in-memory database is not wiped between calls.
    """
    global _mem_conn
    if "memory" in DB_PATH or DB_PATH == ":memory:":
        with _mem_lock:
            if _mem_conn is None:
                uri_mode = DB_PATH.startswith("file:")
                _mem_conn = sqlite3.connect(
                    DB_PATH, check_same_thread=False, uri=uri_mode
                )
                _mem_conn.row_factory = sqlite3.Row
        return _mem_conn
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create the users table if it doesn't exist. Idempotent."""
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT    UNIQUE NOT NULL,
            password TEXT    NOT NULL,
            role     TEXT    NOT NULL DEFAULT 'analyst',
            created  INTEGER NOT NULL
        )
    """)
    conn.commit()


# ── Password hashing (PBKDF2-HMAC-SHA256, no external dep) ───────────────────

_ITERATIONS = 260_000   # OWASP 2024 minimum for PBKDF2-SHA256

# Pre-computed dummy hash — used in login_user to equalise timing between
# "user not found" and "wrong password" paths (exactly one PBKDF2 call each).
# Computed once at module load; never used for actual authentication.
_DUMMY_HASH: str = ""


def _hash_password(password: str, salt: Optional[bytes] = None) -> str:
    """Return a self-describing storable string:  iterations$b64salt$b64hash"""
    if salt is None:
        salt = secrets.token_bytes(16)
    raw = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), salt, _ITERATIONS
    )
    return f"{_ITERATIONS}${base64.b64encode(salt).decode()}${base64.b64encode(raw).decode()}"


def _verify_password(password: str, stored: str) -> bool:
    parts = stored.split("$")
    if len(parts) != 3:
        return False
    iters, b64salt, b64hash = parts
    salt = base64.b64decode(b64salt)
    candidate = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, int(iters))
    return hmac.compare_digest(base64.b64decode(b64hash), candidate)


# ── Minimal JWT (header.payload.signature, HS256) ────────────────────────────
# Clean-room HS256 — avoids PyJWT to minimise the dependency surface and keep
# every line of the mechanism visible and auditable.

def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64url_decode(s: str) -> bytes:
    # (4 - len % 4) % 4 avoids adding 4 '=' when already aligned (len % 4 == 0).
    padding = (4 - len(s) % 4) % 4
    return base64.urlsafe_b64decode(s + "=" * padding)


def _sign(message: str) -> str:
    return _b64url(
        hmac.new(SECRET_KEY.encode(), message.encode(), hashlib.sha256).digest()
    )


def create_token(username: str, role: str) -> str:
    now = int(time.time())
    header = _b64url(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    payload = _b64url(json.dumps({
        "sub": username,
        "role": role,
        "iat": now,
        "exp": now + TOKEN_TTL_SECONDS,
    }).encode())
    signature = _sign(f"{header}.{payload}")
    return f"{header}.{payload}.{signature}"


def decode_token(token: str) -> dict:
    """Decode and validate a token. Raises HTTPException on any failure."""
    try:
        header, payload, signature = token.split(".")
    except ValueError:
        raise HTTPException(status_code=401, detail="Malformed token")

    expected = _sign(f"{header}.{payload}")
    if not hmac.compare_digest(expected, signature):
        raise HTTPException(status_code=401, detail="Invalid token signature")

    try:
        claims = json.loads(_b64url_decode(payload))
    except Exception:
        raise HTTPException(status_code=401, detail="Malformed token payload")

    if claims.get("exp", 0) < int(time.time()):
        raise HTTPException(status_code=401, detail="Token expired")

    return claims


# ── FastAPI dependency injection ──────────────────────────────────────────────

_bearer = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> dict:
    """FastAPI dependency — resolves a Bearer token to a validated claims dict."""
    return decode_token(credentials.credentials)


def require_role(*roles: str):
    """
    Dependency factory that gates a route to one or more specific roles.

    Usage:
        @router.delete("/entity/{id}")
        def delete_entity(id: str, claims: dict = Depends(require_role("admin"))):
            ...
    """
    def _dep(claims: dict = Depends(get_current_user)) -> dict:
        if claims.get("role") not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{claims.get('role')}' is not authorised for this resource.",
            )
        return claims
    return _dep


# ── User CRUD ─────────────────────────────────────────────────────────────────

def register_user(
    username: str,
    password: str,
    role: str = "analyst",
    *,
    allow_admin: bool = False,
) -> dict:
    """
    Create a new user.

    The allow_admin flag must be True for the admin role to be accepted.
    It is only set True by the admin-only promotion endpoint — never by the
    public /register route — preventing unauthenticated privilege escalation.
    """
    if role == "admin" and not allow_admin:
        raise HTTPException(
            status_code=403,
            detail="Self-registration as admin is not permitted. "
                   "Contact an existing admin to have your role promoted.",
        )
    if role not in ROLES:
        raise HTTPException(status_code=400, detail=f"Invalid role '{role}'")
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    if not username or len(username) > 64:
        raise HTTPException(status_code=400, detail="Username must be 1–64 characters")

    hashed = _hash_password(password)
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO users (username, password, role, created) VALUES (?, ?, ?, ?)",
            (username, hashed, role, int(time.time())),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="Username already exists")

    return {"username": username, "role": role}


def login_user(username: str, password: str) -> str:
    """
    Verify credentials and return a signed JWT.

    Timing note: both the "user not found" and "wrong password" paths run
    exactly one PBKDF2-HMAC-SHA256 evaluation (260k iterations). _DUMMY_HASH
    is pre-computed at module load so the missing-user path doesn't incur a
    second hashing round and leak user existence via response time.
    """
    conn = get_db()
    row = conn.execute(
        "SELECT password, role FROM users WHERE username = ?", (username,)
    ).fetchone()

    stored = row["password"] if row else _DUMMY_HASH
    password_ok = _verify_password(password, stored)

    if not row or not password_ok:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return create_token(username, row["role"])


def promote_user(username: str, new_role: str) -> dict:
    """
    Change a user's role. Caller must enforce admin-only access via
    require_role("admin") on the endpoint — this function does not check.
    """
    if new_role not in ROLES:
        raise HTTPException(status_code=400, detail=f"Invalid role '{new_role}'")
    conn = get_db()
    cursor = conn.execute(
        "UPDATE users SET role = ? WHERE username = ?", (new_role, username)
    )
    conn.commit()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail=f"User '{username}' not found")
    return {"username": username, "role": new_role}


def get_user(username: str) -> Optional[dict]:
    conn = get_db()
    row = conn.execute(
        "SELECT username, role, created FROM users WHERE username = ?", (username,)
    ).fetchone()
    return dict(row) if row else None


# ── Module init ───────────────────────────────────────────────────────────────
# Compute the dummy hash once when the module loads.
_DUMMY_HASH = _hash_password("oil_startup_timing_dummy_do_not_use")
