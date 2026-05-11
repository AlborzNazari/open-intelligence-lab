"""
OIL v0.7 — test_user_auth.py   (updated for full schema)
7 tests covering registration, login, JWT integrity, role enforcement,
user enumeration defence, session claims, and token expiry.
"""

import os
os.environ["OIL_USER_DB"]    = "file::memory:?cache=shared"
os.environ["OIL_SECRET_KEY"] = "test-secret-key-do-not-use-in-prod"
os.environ["OIL_TOKEN_TTL"]  = "3600"
os.environ["OIL_MAX_ATTEMPTS"] = "5"
os.environ["OIL_LOCKOUT_SEC"]  = "900"

import time, json, base64, hmac as _hmac, hashlib
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.auth import init_db, decode_token
from backend.auth_router import router as auth_router

@pytest.fixture(scope="module")
def client():
    app = FastAPI()
    app.include_router(auth_router, prefix="/auth", tags=["auth"])
    init_db()
    return TestClient(app)

def _reg(client, username, password="password99", full_name="Test User"):
    client.post("/auth/register", json={"username": username, "password": password, "full_name": full_name})

def _login(client, username, password="password99"):
    r = client.post("/auth/login", json={"username": username, "password": password})
    assert r.status_code == 200, f"login failed: {r.json()}"
    return r.json()["access_token"]

def _expired_token(username, role):
    secret = os.environ["OIL_SECRET_KEY"]
    def b64u(d): return base64.urlsafe_b64encode(d).rstrip(b"=").decode()
    def sign(m): return b64u(_hmac.new(secret.encode(), m.encode(), hashlib.sha256).digest())
    h = b64u(json.dumps({"alg":"HS256","typ":"JWT"}).encode())
    p = b64u(json.dumps({"sub":username,"role":role,"name":"X","iat":int(time.time())-30,"exp":int(time.time())-10}).encode())
    return f"{h}.{p}.{sign(f'{h}.{p}')}"

# ── TEST 1 ────────────────────────────────────────────────────────────────────
def test_register_creates_analyst_with_full_name(client):
    r = client.post("/auth/register", json={"username":"alice","password":"securepass1","full_name":"Alice Smith"})
    assert r.status_code == 201
    u = r.json()["user"]
    assert u["username"] == "alice"
    assert u["full_name"] == "Alice Smith"
    assert u["role"] == "analyst"

# ── TEST 2 ────────────────────────────────────────────────────────────────────
def test_login_returns_jwt_with_name_and_role(client):
    _reg(client, "bob", full_name="Bob Jones")
    token  = _login(client, "bob")
    claims = decode_token(token)
    assert claims["sub"]  == "bob"
    assert claims["role"] == "analyst"
    assert claims["name"] == "Bob Jones"
    assert claims["exp"]  >  int(time.time())

# ── TEST 3 ────────────────────────────────────────────────────────────────────
def test_wrong_password_returns_401_no_token(client):
    _reg(client, "carol", full_name="Carol C")
    r = client.post("/auth/login", json={"username":"carol","password":"wrongpass"})
    assert r.status_code == 401
    assert "access_token" not in r.json()

# ── TEST 4 ────────────────────────────────────────────────────────────────────
def test_unknown_user_returns_401_not_404_no_leak(client):
    r = client.post("/auth/login", json={"username":"ghost_xyz_not_real","password":"x"})
    assert r.status_code == 401
    detail = r.json().get("detail","").lower()
    assert "not found" not in detail
    assert "exist"     not in detail
    assert "no such"   not in detail

# ── TEST 5 ────────────────────────────────────────────────────────────────────
def test_me_returns_full_profile(client):
    _reg(client, "dave", full_name="Dave D")
    token = _login(client, "dave")
    r = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    body = r.json()
    assert body["username"]  == "dave"
    assert body["full_name"] == "Dave D"
    assert body["role"]      == "analyst"

# ── TEST 6 ────────────────────────────────────────────────────────────────────
def test_analyst_forbidden_from_admin_endpoints(client):
    _reg(client, "eve", full_name="Eve E")
    token = _login(client, "eve")
    for path in ["/auth/users", "/auth/audit"]:
        r = client.get(path, headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 403, f"{path} should be 403 for analyst"

# ── TEST 7 ────────────────────────────────────────────────────────────────────
def test_expired_token_rejected_with_correct_detail(client):
    expired = _expired_token("alice", "analyst")
    r = client.get("/auth/me", headers={"Authorization": f"Bearer {expired}"})
    assert r.status_code == 401
    assert "expired" in r.json()["detail"].lower()
