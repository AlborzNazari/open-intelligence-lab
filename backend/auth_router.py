"""
OIL v0.7 — /auth router

Endpoints:
  POST /auth/register       — public, creates analyst account
  POST /auth/login          — public, returns JWT
  GET  /auth/me             — authenticated, returns own profile
  POST /auth/logout         — authenticated, records logout in audit log
  POST /auth/promote        — admin only, change any user's role
  POST /auth/unlock         — admin only, clear lockout on an account
  GET  /auth/users          — admin only, list all users with metadata
  GET  /auth/audit          — admin only, recent audit log

Wire into api/main.py:
    from backend.auth import init_db
    from backend.auth_router import router as auth_router
    init_db()
    app.include_router(auth_router, prefix="/auth", tags=["auth"])
"""

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from typing import Optional

from .auth import (
    register_user, login_user, promote_user, unlock_user,
    get_current_user, get_user, require_role,
    list_users, get_audit_log,
    decode_token,
)
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    username:  str
    password:  str
    full_name: str


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type:   str = "bearer"


class PromoteRequest(BaseModel):
    username: str
    role:     str


class UnlockRequest(BaseModel):
    username: str


# ── Public endpoints ──────────────────────────────────────────────────────────

@router.post("/register", status_code=201)
def register(body: RegisterRequest, request: Request):
    """
    Create a new analyst account.
    Admin accounts can only be created via POST /auth/promote by an existing admin.
    """
    user = register_user(
        body.username, body.password, body.full_name,
        role="analyst", request=request,
    )
    return {"message": "Account created", "user": user}


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, request: Request):
    """Exchange credentials for a signed JWT. Locks account after 5 failures."""
    token = login_user(body.username, body.password, request=request)
    return TokenResponse(access_token=token)


# ── Authenticated endpoints ───────────────────────────────────────────────────

@router.get("/me")
def me(claims: dict = Depends(get_current_user)):
    """Return the authenticated user's full profile from the database."""
    user = get_user(claims["sub"])
    if not user:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/logout", status_code=200)
def logout(request: Request, claims: dict = Depends(get_current_user)):
    """Record a logout event in the audit log. Token invalidation is client-side."""
    from .auth import _audit, _get_ip
    _audit(claims["sub"], "logout", _get_ip(request))
    return {"message": "Logged out"}


# ── Admin endpoints ───────────────────────────────────────────────────────────

@router.post("/promote", status_code=200)
def promote(body: PromoteRequest, request: Request, claims: dict = Depends(require_role("admin"))):
    """Change a user's role. Admin only."""
    result = promote_user(body.username, body.role, acting_admin=claims["sub"], request=request)
    return {"message": f"'{result['username']}' is now '{result['role']}'", "user": result}


@router.post("/unlock", status_code=200)
def unlock(body: UnlockRequest, request: Request, claims: dict = Depends(require_role("admin"))):
    """Clear a locked account. Admin only."""
    result = unlock_user(body.username, acting_admin=claims["sub"], request=request)
    return {"message": f"'{body.username}' has been unlocked", "user": result}


@router.get("/users")
def users(claims: dict = Depends(require_role("admin"))):
    """List all users with full metadata. Admin only."""
    return {"users": list_users()}


@router.get("/audit")
def audit(limit: int = 100, claims: dict = Depends(require_role("admin"))):
    """Return the most recent audit log entries. Admin only."""
    return {"events": get_audit_log(limit=min(limit, 500))}
