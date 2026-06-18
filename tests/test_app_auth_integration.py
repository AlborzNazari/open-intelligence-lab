"""
tests/test_app_auth_integration.py

Integration tests that run against the REAL application object (api.main.app),
not a hand-built throwaway FastAPI() instance. This is the test that catches the
class of bug where auth.py and auth_router.py are correct in isolation but never
actually wired into the running app.

Covers:
  1. /auth router is mounted on the real app (register + login work end-to-end)
  2. Intelligence endpoints reject unauthenticated requests
  3. Intelligence endpoints accept a valid analyst token
  4. A garbage token is still rejected on the real app
"""

import pytest
from fastapi.testclient import TestClient

from api.main import app

# One protected endpoint used as the canary for the auth gate.
PROTECTED = "/intelligence/graph/summary"


@pytest.fixture(scope="module")
def client():
    # Context-manager form runs the lifespan, which calls init_db() on the real app.
    with TestClient(app) as c:
        yield c


def _register_and_login(client, username="int_analyst", password="password99"):
    client.post(
        "/auth/register",
        json={"username": username, "password": password, "full_name": "Integration Analyst"},
    )
    r = client.post("/auth/login", json={"username": username, "password": password})
    assert r.status_code == 200, f"login failed on real app: {r.status_code} {r.text}"
    return r.json()["access_token"]


def test_auth_router_is_mounted_on_real_app(client):
    r = client.post(
        "/auth/register",
        json={"username": "wired_check", "password": "password99", "full_name": "Wired Check"},
    )
    # 201 created or 409 already-exists both prove the route exists. A 404 here
    # would mean auth was never wired into api.main.
    assert r.status_code in (201, 409), f"/auth/register missing on real app: {r.status_code}"


def test_intelligence_blocked_without_token(client):
    r = client.get(PROTECTED)
    assert r.status_code in (401, 403), (
        f"{PROTECTED} returned {r.status_code} without a token. "
        f"The intelligence router is NOT protected."
    )


def test_intelligence_allowed_with_valid_token(client):
    token = _register_and_login(client)
    r = client.get(PROTECTED, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200, (
        f"{PROTECTED} returned {r.status_code} with a valid token: {r.text}"
    )


def test_intelligence_rejects_garbage_token(client):
    r = client.get(PROTECTED, headers={"Authorization": "Bearer not.a.real.token"})
    assert r.status_code == 401, (
        f"{PROTECTED} accepted a garbage token (got {r.status_code})."
    )
