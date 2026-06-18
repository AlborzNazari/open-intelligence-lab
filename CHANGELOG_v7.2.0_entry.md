## [v7.2.0] - 2026-06-17 - Authentication Enforcement and Repo Cleanup

Security and hygiene release. The auth module that already existed (PBKDF2-SHA256,
HS256 JWTs, account lockout, RBAC, audit log) is now actually wired into the
running application, so every intelligence endpoint is authenticated for the
first time. Alongside that, this release removes dead code, drops unused
dependencies, fixes a silently broken risk factor, and collapses scattered
version strings into a single source of truth. The auth enforcement is a
breaking change: any client must now send a Bearer token.

### Security
- All `/intelligence/*` endpoints moved from open to authenticated. They now
  require a valid JWT carrying an analyst or admin role, enforced at the router
  level so no individual route can ship unguarded. BREAKING for existing clients
  and for the dashboard, which must now authenticate.

### Added
- Auth router mounted at `/auth`: `register`, `login`, `logout`, `me`,
  `promote`, `unlock`, `users`, `audit`. Before this release none of these
  routes existed on the running app.
- `init_db()` now runs on startup so the auth database is ready before the first
  request.
- `tests/test_app_auth_integration.py`: integration tests that run against the
  real `api.main.app` (not a throwaway instance). Verifies the auth router is
  mounted, unauthenticated requests get 401, valid tokens get 200, and forged
  tokens are rejected. This is the test that would have caught the original gap.
- `tests/conftest.py`: pins the auth environment before any test import, removing
  an order-dependent `SECRET_KEY` failure in the suite.
- `visualization/.gitkeep`: keeps the Cloudflare Workers asset directory tracked
  in git now that the orphaned renderer is gone.

### Fixed
- `main.py` never wired auth in. The auth module was correct in isolation but the
  app imported none of it, so the running server had zero `/auth` routes and
  every intelligence endpoint was unauthenticated. Now wired.
- `StaticFiles` was used in `main.py` but never imported, failing silently inside
  a bare `try/except`. Import added.
- `risk_analyzer` counted incident neighbors using an `entity_type` key the graph
  never stores, against an `incident_category` type that does not exist in the
  data, so that factor was always zero. Dead branch removed. Risk is now honestly
  base score plus graph connectivity, capped at 1.0.
- `EntityType` listed `organization`, `domain`, and `incident_category`, none of
  which exist in the datasets. Corrected to the real types: `threat_actor`,
  `malware`, `infrastructure`, `vulnerability`, `target_sector`, `attack_pattern`.
- `tests/test_api_endpoints.py` now logs in and sends a token, since the endpoints
  it covers are no longer public.

### Changed
- One `API_VERSION` constant (`7.2.0`) is now the single source of truth, served
  by `/`, `/health`, and `/docs`. Removed the scattered `0.6.1` strings.
- `fly.toml` build `VERSION` aligned to `v7.2.0`.
- `demo.py` documented and confirmed to write its dashboard into `visualization/`,
  which is the Cloudflare Workers deploy target defined in `wrangler.jsonc`.

### Removed
- `api/intelligence_api.py`: orphaned legacy standalone API, imported by nothing,
  superseded by `api/main.py` and the intelligence router.
- `visualization/graph_renderer.py`: orphaned renderer, imported by nothing;
  `demo.py` builds the dashboard itself.
- `api/intelligence/schemas.py`: the unused `RiskResponse` model, referenced
  nowhere.
- `graph_builder.load_from_iterables` and its now-unused typing imports.
- Four unused dependencies from `requirements.txt`: `matplotlib`, `plotly`,
  `pyvis`, `pandas`. The live API uses only `fastapi`, `uvicorn`, `networkx`.

### Known and follow-ups
- Roles are two-tier (`analyst`, `admin`), not the viewer/editor/admin tier
  described in earlier drafts. Article copy should match the code.
- There is no resource-ownership model. CWE-282 does not apply to shared
  reference data here, so the docs should not claim per-object ownership checks.
- `OIL_SECRET_KEY` must be set as a Fly secret, or JWTs will not survive a
  restart because the key is regenerated per process.
- The repo has no `.gitignore`, which is why a full `venv/` was committed. Adding
  one is the next cleanup.
- `campaigns.json` and `mitre_mapping.json` are validated and used by the STIX
  exporter but are not loaded into the live knowledge graph. Either wire them in
  or stop describing them as part of the running API.
