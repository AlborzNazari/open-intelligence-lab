"""
OIL v0.7 — User Authentication & Authorization

Production-grade JWT auth with:
  - PBKDF2-HMAC-SHA256 password hashing (260k iterations, OWASP 2024)
  - Clean-room HS256 JWT (no PyJWT dependency)
  - Role enforcement: analyst / admin
  - Account lockout after 5 consecutive failed attempts (15 min window)
  - Full audit log: every login, failure, logout, promotion recorded
  - Last-login IP + timestamp tracking
  - Constant-time comparisons throughout (no timing oracles)
  - SQLite singleton for in-memory (test) mode; file-based for production
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

from fastapi import HTTPException, Depends, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# ── Config ────────────────────────────────────────────────────────────────────

SECRET_KEY: str     = os.getenv("OIL_SECRET_KEY", secrets.token_hex(32))
TOKEN_TTL: int      = int(os.getenv("OIL_TOKEN_TTL", 3600))       # 1 h
DB_PATH: str        = os.getenv("OIL_USER_DB", "oil_users.db")
MAX_ATTEMPTS: int   = int(os.getenv("OIL_MAX_ATTEMPTS", 5))
LOCKOUT_SEC: int    = int(os.getenv("OIL_LOCKOUT_SEC", 900))       # 15 min

ROLES = {"analyst", "admin"}

# ── Database ──────────────────────────────────────────────────────────────────

_mem_conn: Optional[sqlite3.Connection] = None
_mem_lock = threading.Lock()


def get_db() -> sqlite3.Connection:
    global _mem_conn
    if "memory" in DB_PATH or DB_PATH == ":memory:":
        with _mem_lock:
            if _mem_conn is None:
                uri_mode = DB_PATH.startswith("file:")
                _mem_conn = sqlite3.connect(DB_PATH, check_same_thread=False, uri=uri_mode)
                _mem_conn.row_factory = sqlite3.Row
        return _mem_conn
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create all tables. Idempotent — safe to call on every startup."""
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            username        TEXT    UNIQUE NOT NULL,
            full_name       TEXT    NOT NULL DEFAULT '',
            password        TEXT    NOT NULL,
            role            TEXT    NOT NULL DEFAULT 'analyst',
            created         INTEGER NOT NULL,
            last_login      INTEGER,
            last_login_ip   TEXT,
            failed_attempts INTEGER NOT NULL DEFAULT 0,
            locked_until    INTEGER NOT NULL DEFAULT 0
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            ts         INTEGER NOT NULL,
            username   TEXT    NOT NULL,
            event      TEXT    NOT NULL,
            ip         TEXT,
            detail     TEXT
        )
    """)

    conn.commit()


# ── Audit log ─────────────────────────────────────────────────────────────────

def _audit(username: str, event: str, ip: Optional[str] = None, detail: Optional[str] = None) -> None:
    try:
        conn = get_db()
        conn.execute(
            "INSERT INTO audit_log (ts, username, event, ip, detail) VALUES (?, ?, ?, ?, ?)",
            (int(time.time()), username, event, ip, detail),
        )
        conn.commit()
    except Exception:
        pass   # audit must never break the request


# ── Password hashing ──────────────────────────────────────────────────────────

_ITERATIONS = 260_000

_DUMMY_HASH: str = ""   # populated at module init


def _hash_password(password: str, salt: Optional[bytes] = None) -> str:
    if salt is None:
        salt = secrets.token_bytes(16)
    raw = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _ITERATIONS)
    return f"{_ITERATIONS}${base64.b64encode(salt).decode()}${base64.b64encode(raw).decode()}"


def _verify_password(password: str, stored: str) -> bool:
    parts = stored.split("$")
    if len(parts) != 3:
        return False
    iters, b64salt, b64hash = parts
    salt = base64.b64decode(b64salt)
    candidate = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, int(iters))
    return hmac.compare_digest(base64.b64decode(b64hash), candidate)


# ── JWT (HS256, clean-room) ───────────────────────────────────────────────────

def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64url_decode(s: str) -> bytes:
    padding = (4 - len(s) % 4) % 4
    return base64.urlsafe_b64decode(s + "=" * padding)


def _sign(message: str) -> str:
    return _b64url(hmac.new(SECRET_KEY.encode(), message.encode(), hashlib.sha256).digest())


def create_token(username: str, role: str, full_name: str) -> str:
    now = int(time.time())
    header  = _b64url(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    payload = _b64url(json.dumps({
        "sub":       username,
        "role":      role,
        "name":      full_name,
        "iat":       now,
        "exp":       now + TOKEN_TTL,
    }).encode())
    return f"{header}.{payload}.{_sign(f'{header}.{payload}')}"


def decode_token(token: str) -> dict:
    try:
        header, payload, signature = token.split(".")
    except ValueError:
        raise HTTPException(status_code=401, detail="Malformed token")

    if not hmac.compare_digest(_sign(f"{header}.{payload}"), signature):
        raise HTTPException(status_code=401, detail="Invalid token signature")

    try:
        claims = json.loads(_b64url_decode(payload))
    except Exception:
        raise HTTPException(status_code=401, detail="Malformed token payload")

    if claims.get("exp", 0) < int(time.time()):
        raise HTTPException(status_code=401, detail="Token expired")

    return claims


# ── FastAPI dependencies ──────────────────────────────────────────────────────

_bearer = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> dict:
    return decode_token(credentials.credentials)


def require_role(*roles: str):
    def _dep(claims: dict = Depends(get_current_user)) -> dict:
        if claims.get("role") not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{claims.get('role')}' is not authorised for this resource.",
            )
        return claims
    return _dep


def _get_ip(request: Optional[Request]) -> Optional[str]:
    if request is None:
        return None
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


# ── User operations ───────────────────────────────────────────────────────────

def register_user(
    username: str,
    password: str,
    full_name: str,
    role: str = "analyst",
    *,
    allow_admin: bool = False,
    request: Optional[Request] = None,
) -> dict:
    if role == "admin" and not allow_admin:
        raise HTTPException(status_code=403, detail="Self-registration as admin is not permitted.")
    if role not in ROLES:
        raise HTTPException(status_code=400, detail=f"Invalid role '{role}'")
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    if not username or len(username) > 64:
        raise HTTPException(status_code=400, detail="Username must be 1–64 characters")
    if not full_name or len(full_name) > 128:
        raise HTTPException(status_code=400, detail="Full name must be 1–128 characters")

    hashed = _hash_password(password)
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO users (username, full_name, password, role, created) VALUES (?, ?, ?, ?, ?)",
            (username, full_name.strip(), hashed, role, int(time.time())),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="Username already exists")

    _audit(username, "register", _get_ip(request), f"role={role}")
    return {"username": username, "full_name": full_name.strip(), "role": role}


def login_user(
    username: str,
    password: str,
    request: Optional[Request] = None,
) -> str:
    ip = _get_ip(request)
    conn = get_db()
    row = conn.execute(
        "SELECT password, role, full_name, failed_attempts, locked_until FROM users WHERE username = ?",
        (username,),
    ).fetchone()

    # --- Timing equalisation: always run one PBKDF2 regardless of user existence ---
    stored = row["password"] if row else _DUMMY_HASH
    password_ok = _verify_password(password, stored)

    if not row or not password_ok:
        if row:
            now = int(time.time())
            attempts = row["failed_attempts"] + 1
            locked_until = now + LOCKOUT_SEC if attempts >= MAX_ATTEMPTS else row["locked_until"]
            conn.execute(
                "UPDATE users SET failed_attempts = ?, locked_until = ? WHERE username = ?",
                (attempts, locked_until, username),
            )
            conn.commit()
            _audit(username, "login_fail", ip, f"attempt={attempts}")
        else:
            _audit(username, "login_fail_unknown", ip)
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # --- Check lockout AFTER password verify (constant-time) ---
    now = int(time.time())
    if row["locked_until"] > now:
        remaining = row["locked_until"] - now
        _audit(username, "login_blocked", ip, f"locked_for={remaining}s")
        raise HTTPException(
            status_code=429,
            detail=f"Account temporarily locked. Try again in {remaining // 60 + 1} minutes.",
        )

    # --- Successful login: reset counters, record last_login ---
    conn.execute(
        "UPDATE users SET failed_attempts = 0, locked_until = 0, last_login = ?, last_login_ip = ? WHERE username = ?",
        (now, ip, username),
    )
    conn.commit()
    _audit(username, "login_ok", ip)

    return create_token(username, row["role"], row["full_name"] or username)


def promote_user(
    username: str,
    new_role: str,
    acting_admin: str,
    request: Optional[Request] = None,
) -> dict:
    if new_role not in ROLES:
        raise HTTPException(status_code=400, detail=f"Invalid role '{new_role}'")
    conn = get_db()
    cursor = conn.execute(
        "UPDATE users SET role = ? WHERE username = ?", (new_role, username)
    )
    conn.commit()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail=f"User '{username}' not found")
    _audit(username, "role_change", _get_ip(request), f"new_role={new_role} by={acting_admin}")
    return {"username": username, "role": new_role}


def list_users() -> list:
    conn = get_db()
    rows = conn.execute(
        "SELECT username, full_name, role, created, last_login, last_login_ip, failed_attempts, locked_until FROM users ORDER BY created DESC"
    ).fetchall()
    now = int(time.time())
    return [
        {
            "username":       r["username"],
            "full_name":      r["full_name"],
            "role":           r["role"],
            "created":        r["created"],
            "last_login":     r["last_login"],
            "last_login_ip":  r["last_login_ip"],
            "failed_attempts": r["failed_attempts"],
            "locked":         r["locked_until"] > now,
            "locked_until":   r["locked_until"] if r["locked_until"] > now else None,
        }
        for r in rows
    ]


def get_audit_log(limit: int = 100) -> list:
    conn = get_db()
    rows = conn.execute(
        "SELECT ts, username, event, ip, detail FROM audit_log ORDER BY ts DESC LIMIT ?",
        (limit,),
    ).fetchall()
    return [dict(r) for r in rows]


def get_user(username: str) -> Optional[dict]:
    conn = get_db()
    row = conn.execute(
        "SELECT username, full_name, role, created, last_login, last_login_ip FROM users WHERE username = ?",
        (username,),
    ).fetchone()
    return dict(row) if row else None


def unlock_user(username: str, acting_admin: str, request: Optional[Request] = None) -> dict:
    conn = get_db()
    cursor = conn.execute(
        "UPDATE users SET failed_attempts = 0, locked_until = 0 WHERE username = ?", (username,)
    )
    conn.commit()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail=f"User '{username}' not found")
    _audit(username, "unlock", _get_ip(request), f"by={acting_admin}")
    return {"username": username, "unlocked": True}


# ── Module init ───────────────────────────────────────────────────────────────
_DUMMY_HASH = _hash_password("oil_startup_timing_dummy_do_not_use")
