# v0.7.0 — User Authentication and Authorisation

First release with a real identity layer, wired into the running app so that every intelligence endpoint is now authenticated.

## Highlights

- Clean-room JWT authentication, no third-party library. HS256 signing and verification implemented directly on the Python standard library.
- PBKDF2-HMAC-SHA256 password hashing, 260,000 iterations, a random 16-byte salt per user.
- SQLite user store with account lockout: 5 consecutive failed logins lock the account for 15 minutes.
- Audit log table recording every login, failed login, lockout, logout, role change, and unlock, each with IP address and timestamp.
- 8 endpoints under the `/auth` prefix: `register`, `login`, `me`, `logout`, `promote`, `unlock`, `users`, `audit`.
- `auth.html`, a full auth portal (register, login, identity card, bearer-token preview, admin panel) served at `/ui/auth.html` on the live Fly.io deployment.

## Wired into the app

- `api/main.py` now runs `init_db()` on startup, mounts the auth router at `/auth`, and guards every `/intelligence/*` route with `require_role("analyst", "admin")`.
- Fixed the `StaticFiles` import so `/ui/auth.html` is actually served instead of failing silently.
- Collapsed scattered version strings into a single `API_VERSION` constant.

## Security properties

- Timing oracle defence: a module-level `_DUMMY_HASH` means the unknown-user path and the wrong-password path run the same PBKDF2 work and take the same time, so login timing does not reveal whether a username exists.
- Admin self-registration blocked: `register_user` defaults `allow_admin=False`, so public `/register` can only create an `analyst`. The `admin` role is assignable only by an existing admin via `/promote`, which returns 403 otherwise.
- Base64url padding fix: `padding = (4 - len(s) % 4) % 4`, so an already-aligned string is never given four spurious `=` characters during token decode.
- Deterministic tests: an in-memory SQLite singleton via `file::memory:?cache=shared` keeps one shared connection alive, so the database is not wiped between test fixture calls.

## Tests

Seven auth unit tests in `test_user_auth.py`, bringing the full suite to 121 passing:

- `test_register_creates_analyst_with_full_name`
- `test_login_returns_jwt_with_name_and_role`
- `test_wrong_password_returns_401_no_token`
- `test_unknown_user_returns_401_not_404_no_leak` (user enumeration defence)
- `test_me_returns_full_profile`
- `test_analyst_forbidden_from_admin_endpoints`
- `test_expired_token_rejected_with_correct_detail`

Plus a separate integration test file, `test_app_auth_integration.py` (4 tests), that runs against the real `api.main.app` and proves auth is wired in: the `/auth` router is mounted, a tokenless request returns 401, a valid token returns 200, and a forged token is rejected.

Behaviour versus coverage: account lockout (returns 429), the duplicate-username guard (returns 409), and audit logging are all implemented and live. They are exercised through the `auth.py` functions rather than by a dedicated case in `test_user_auth.py`.

## Breaking change

Authentication is now enforced. Every `/intelligence/*` endpoint requires a Bearer token carrying an `analyst` or `admin` role. Existing API clients and the dashboard must authenticate before they can read data.

## Upgrade notes

- Set `OIL_SECRET_KEY` as a Fly secret in production, or JWTs will reset on every restart because the key is regenerated per process.
- Keep `oil_users.db` out of version control. It holds password hashes.
