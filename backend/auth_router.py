"""
OIL v0.7 — /auth router
Wire this into backend/main.py with:
    from backend.auth import init_db
    from backend.auth_router import router as auth_router
    init_db()
    app.include_router(auth_router, prefix="/auth", tags=["auth"])
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from .auth import register_user, login_user, promote_user, get_current_user, require_role

router = APIRouter()


# ── Request / response schemas ────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    username: str
    password: str
    # Public registration is always analyst; role field intentionally absent.
    # Admins use the /promote endpoint to elevate existing users.


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class PromoteRequest(BaseModel):
    username: str
    role: str


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/register", status_code=201)
def register(body: RegisterRequest):
    """
    Register a new analyst account (public endpoint).
    Admin accounts can only be created via POST /auth/promote by an existing admin.
    """
    user = register_user(body.username, body.password, role="analyst")
    return {"message": "User created", "user": user}


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest):
    """Exchange credentials for a signed JWT (1-hour TTL by default)."""
    token = login_user(body.username, body.password)
    return TokenResponse(access_token=token)


@router.get("/me")
def me(claims: dict = Depends(get_current_user)):
    """Return the currently authenticated user's identity and role."""
    return {"username": claims["sub"], "role": claims["role"]}


@router.post("/promote", status_code=200)
def promote(body: PromoteRequest, claims: dict = Depends(require_role("admin"))):
    """
    Change a user's role. Admin-only.
    This is the only way to create or demote admin accounts.
    """
    result = promote_user(body.username, body.role)
    return {"message": f"User '{result['username']}' is now '{result['role']}'", "user": result}


@router.get("/admin-only")
def admin_panel(claims: dict = Depends(require_role("admin"))):
    """Demonstration of an admin-gated route."""
    return {"message": f"Welcome to the admin panel, {claims['sub']}"}
