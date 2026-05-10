"""
OIL v0.7 — test_user_auth.py
7 new tests covering the user authentication and authorisation surface.

Run with:
    pytest tests/test_user_auth.py -v

Dependencies already in the project: pytest, fastapi, httpx (starlette TestClient).

SQLite note: we use 'file::memory:?cache=shared' (URI mode) instead of ':memory:'
so that all calls to get_db() within the same process share one in-memory database.
Plain ':memory:' creates an isolated database per connection — every get_db() call
would see an empty DB, making register→login round-trips impossible.
"""

import os
# Set env vars BEFORE importing backend modules — module-level constants
# (SECRET_KEY, TOKEN_TTL_SECONDS, DB_PATH) are evaluated at import time.
os.environ["OIL_USER_DB"] = "file::memory:?cache=shared"
os.environ["OIL_SECRET_KEY"] = "test-secret-key-do-not-use-in-prod"
os.environ["OIL_TOKEN_TTL"] = "3600"

import time
import json
import base64
import hmac as _hmac
import hashlib
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.auth import init_db, decode_token, create_token
from backend.auth_router import router as auth_router


# ── App + client fixtures ─────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def app():
    application = FastAPI()
    application.include_router(auth_router, prefix="/auth", tags=["auth"])
    init_db()
    return application


@pytest.fixture(scope="module")
def client(app):
    return TestClient(app)


# ── Helper ────────────────────────────────────────────────────────────────────

def _register_and_login(client, username: str, password: str) -> str:
    """Register a user and return a valid access token for them."""
    client.post("/auth/register", json={"username": username, "password": password})
    resp = client.post("/auth/login", json={"username": username, "password": password})
    assert resp.status_code == 200, f"Login failed for {username}: {resp.json()}"
    return resp.json()["access_token"]


def _make_expired_token(username: str, role: str) -> str:
    """Craft a structurally valid, correctly signed token whose exp is in the past."""
    secret = os.environ["OIL_SECRET_KEY"]

    def b64url(data: bytes) -> str:
        return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

    def sign(msg: str) -> str:
        return b64url(_hmac.new(secret.encode(), msg.encode(), hashlib.sha256).digest())

    header = b64url(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    payload = b64url(json.dumps({
        "sub": username,
        "role": role,
        "iat": int(time.time()) - 20,
        "exp": int(time.time()) - 10,   # 10 seconds in the past
    }).encode())
    return f"{header}.{payload}.{sign(f'{header}.{payload}')}"


# ═══════════════════════════════════════════════════════════════════════════════
# TEST 1 — Successful registration creates a user with the expected role
# ═══════════════════════════════════════════════════════════════════════════════

def test_register_creates_analyst_user(client):
    """
    POST /auth/register with valid credentials should return 201 and echo back
    the username. Role must be 'analyst' — public registration cannot self-assign admin.
    """
    resp = client.post("/auth/register", json={
        "username": "alice",
        "password": "securepass1",
    })
    assert resp.status_code == 201
    body = resp.json()
    assert body["user"]["username"] == "alice"
    assert body["user"]["role"] == "analyst"


# ═══════════════════════════════════════════════════════════════════════════════
# TEST 2 — Login with valid credentials returns a well-formed JWT
# ═══════════════════════════════════════════════════════════════════════════════

def test_login_returns_valid_jwt(client):
    """
    POST /auth/login with correct credentials should return a JWT that:
    - is non-empty
    - decodes to the correct subject and role
    - carries an exp timestamp in the future
    """
    client.post("/auth/register", json={"username": "bob", "password": "password99"})
    resp = client.post("/auth/login", json={"username": "bob", "password": "password99"})
    assert resp.status_code == 200

    token = resp.json()["access_token"]
    assert token

    claims = decode_token(token)
    assert claims["sub"] == "bob"
    assert claims["role"] == "analyst"
    assert claims["exp"] > int(time.time())


# ═══════════════════════════════════════════════════════════════════════════════
# TEST 3 — Wrong password is rejected with 401, no token in response
# ═══════════════════════════════════════════════════════════════════════════════

def test_wrong_password_returns_401(client):
    """
    POST /auth/login with a wrong password must return 401.
    The response body must not contain a token — guards against accidentally
    leaking a token alongside an error status code.
    """
    client.post("/auth/register", json={"username": "carol", "password": "realpassword1"})
    resp = client.post("/auth/login", json={"username": "carol", "password": "wrongpassword"})

    assert resp.status_code == 401
    assert "access_token" not in resp.json()
    assert "token" not in resp.json()


# ═══════════════════════════════════════════════════════════════════════════════
# TEST 4 — Non-existent user gets 401, not 404, with a non-leaking error message
# ═══════════════════════════════════════════════════════════════════════════════

def test_unknown_user_returns_401_not_404(client):
    """
    Login for a user that was never registered must return 401, not 404.
    Returning 404 is a user enumeration oracle — an attacker can use it to
    determine which usernames exist before attempting password attacks.
    The error message must also not distinguish the two failure modes.
    """
    resp = client.post("/auth/login", json={
        "username": "ghost_user_that_does_not_exist",
        "password": "doesntmatter",
    })
    assert resp.status_code == 401
    detail = resp.json().get("detail", "")
    assert "not found" not in detail.lower()
    assert "exist" not in detail.lower()
    assert "no such" not in detail.lower()


# ═══════════════════════════════════════════════════════════════════════════════
# TEST 5 — Authenticated /me endpoint returns the correct user claims
# ═══════════════════════════════════════════════════════════════════════════════

def test_me_endpoint_returns_correct_claims(client):
    """
    GET /auth/me with a valid Bearer token should return the username and role
    exactly as they were set at registration time — full round-trip validation.
    """
    token = _register_and_login(client, "dave", "davepass12")
    resp = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["username"] == "dave"
    assert body["role"] == "analyst"


# ═══════════════════════════════════════════════════════════════════════════════
# TEST 6 — Analyst is forbidden from admin-only endpoints (role enforcement)
# ═══════════════════════════════════════════════════════════════════════════════

def test_analyst_cannot_access_admin_endpoint(client):
    """
    An authenticated analyst hitting an admin-gated route must get 403 Forbidden.
    This validates the require_role() dependency factory end-to-end.
    401 would mean 'not authenticated'; we want 403 = 'authenticated but not authorised'.
    """
    token = _register_and_login(client, "eve", "evepass12")
    resp = client.get("/auth/admin-only", headers={"Authorization": f"Bearer {token}"})

    assert resp.status_code == 403
    detail = resp.json().get("detail", "")
    assert "authorised" in detail.lower()


# ═══════════════════════════════════════════════════════════════════════════════
# TEST 7 — Expired token is rejected with 401 "Token expired"
# ═══════════════════════════════════════════════════════════════════════════════

def test_expired_token_is_rejected(client):
    """
    A token with a valid signature but exp in the past must be rejected with 401.
    We craft one directly (valid HMAC, correct structure, exp = now - 10s) to
    confirm that the TTL check is evaluated independently of signature validity.
    This guards against the 'alg:none' class of vulnerabilities where signature
    checks pass but time checks are skipped.
    """
    expired_token = _make_expired_token("alice", "analyst")
    resp = client.get("/auth/me", headers={"Authorization": f"Bearer {expired_token}"})

    assert resp.status_code == 401
    assert "expired" in resp.json()["detail"].lower()
