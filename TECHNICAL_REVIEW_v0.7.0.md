# Open Intelligence Lab v0.7.0 — Technical Review and Architecture

A factual walkthrough of what the software is, what changed, how each piece works, and an honest assessment of where it stands against words like "secure," "enterprise," and "robust." Nothing here is aspirational. Every claim maps to code in the repo.

---

## 1. The breaking change, concretely

**Before v0.7.0.** The API was open. Any client could call `GET /intelligence/entities`, `/graph/summary`, `/graph/edges`, or `/analyze/{id}` and get data back, no identity required. The auth module existed in `backend/auth.py` but was never imported by `api/main.py`, so the `/auth` routes did not exist on the running server and no route checked a token. The dashboard worked because it just fetched open endpoints.

**After v0.7.0.** `api/main.py` mounts the auth router and wraps the entire intelligence router in `Depends(require_role("analyst", "admin"))`. Now every `/intelligence/*` request is checked before the handler runs. No token, or a bad token, returns 401 before any data is touched.

**What "breaking" means in practice.** A breaking change is one that forces existing callers to change to keep working. Here, every current consumer that worked yesterday now fails:

- The public dashboard (`index.html`) sends its fetches with no `Authorization` header. After this release it receives 401 on every call and renders empty. This is a real, present regression, not a theoretical one.
- Any script, integration, or saved request that hit the intelligence endpoints now needs to register, log in, and attach a Bearer token.

That is exactly why this is a minor-version bump in 0.x terms (or a major bump after 1.0): the contract changed in a way that is not backward compatible.

---

## 2. System architecture: components and their duties

The system is layered. Each layer has one job and talks only to the layer below it.

### Presentation layer
- **`index.html`** — the Visual Lab dashboard (graph view, entity table, attack-pattern grid, STIX export buttons, API probe). Currently auth-blind (see section 7).
- **`auth.html`** — the auth portal (register, login, identity card, token preview, admin panel). Served at `/ui/auth.html`.

### API layer (`api/`)
- **`api/main.py`** — the composition root. Creates the FastAPI app, configures CORS, runs `init_db()` on startup, optionally starts the MISP feed scheduler, mounts the auth router at `/auth`, guards and mounts the intelligence router, and serves the static UI at `/ui`. This is the only file that knows how all the pieces wire together.
- **`api/intelligence/router.py`** — HTTP surface for intelligence: five read-only GET endpoints. Validates query parameters, calls the service, shapes responses. Knows nothing about how the graph is built.
- **`api/intelligence/service.py`** — orchestration. Loads the graph and analyzers once and caches them (`lru_cache` singletons), then answers router calls. This is the seam between HTTP and the engine.

### Domain engine (`core_engine/`)
- **`graph_builder.py`** — builds a NetworkX directed graph from the JSON datasets (entities, attack patterns, relations). Also exposes a small programmatic construction API (`add_entity`, `add_relationship`).
- **`risk_analyzer.py`** — computes a risk score per node from base risk plus graph connectivity, capped at 1.0, and writes the score back onto the node.
- **`intelligence_explainer.py`** — turns a node and its score into a plain-language rationale and a verdict band (LOW/MEDIUM/HIGH/CRITICAL).
- **`intelligence_entities.py`** — the typed value object and the `EntityType` set used by the programmatic construction API.

### Security layer (`backend/auth*.py`)
- **`backend/auth.py`** — all the security primitives: SQLite user store, PBKDF2 hashing, clean-room HS256 JWT encode/decode, lockout logic, audit logging, the `get_current_user` and `require_role` dependencies, and `init_db`.
- **`backend/auth_router.py`** — the eight `/auth` HTTP endpoints, thin wrappers over `auth.py`.

### Intelligence ingestion and interop (`backend/`)
- **`stix_exporter.py`** — converts the datasets into STIX 2.1 bundles.
- **`taxii_server.py`** — a separate FastAPI app exposing a TAXII 2.1 feed (publisher). Not started by `api/main.py`; runs as its own process.
- **`taxii_ingestor.py`**, **`misp_client.py`**, **`feed_scheduler.py`**, **`provenance.py`** — the inbound feed pipeline. `feed_scheduler` is started from `main.py`'s lifespan only when `MISP_URL` and `MISP_KEY` are set.

### Data and infrastructure
- **`datasets/`** — five JSON files. The live graph loads three of them (entities, attack patterns, relations). `campaigns.json` and `mitre_mapping.json` are used by the STIX exporter but are not loaded into the live graph.
- **`Dockerfile`, `docker-compose.yml`, `fly.toml`, `wrangler.jsonc`, `.gitlab-ci.yml`** — deploy and CI. The app deploys to Fly.io as `api.main:app`; `wrangler.jsonc` ships `./visualization` (the generated dashboard) to Cloudflare Workers.

---

## 3. The authenticated request lifecycle

A read of `GET /intelligence/graph/summary` after v0.7.0:

1. Request arrives at the FastAPI app with an `Authorization: Bearer <jwt>` header.
2. The router-level dependency `require_role("analyst", "admin")` runs first. It calls `get_current_user`, which extracts the token, verifies the HS256 signature against `SECRET_KEY`, checks `exp`, and returns the claims. If any step fails, it raises 401 and the handler never runs.
3. `require_role` checks that `claims["role"]` is in the allowed set. If not, 403.
4. Only now does the endpoint run. It calls the service.
5. The service returns the cached graph (built once, on first call) and reads the summary off it.
6. The router shapes the JSON and returns 200.

The key architectural property: authorisation is enforced once, at the router boundary, so a new endpoint added to the intelligence router inherits the guard automatically and cannot accidentally ship open.

---

## 4. How authentication works, mechanism by mechanism

This maps each release highlight to its actual implementation.

**Clean-room HS256 JWT.** No PyJWT. A token is `base64url(header).base64url(payload).base64url(signature)`. The signature is `HMAC-SHA256(secret, header.payload)`. Verification recomputes the HMAC and compares with `hmac.compare_digest` (constant time), then checks `exp`. Payload claims: `sub` (username), `role`, `name`, `iat`, `exp`.

**PBKDF2-HMAC-SHA256 password hashing.** On registration the password is run through PBKDF2 with 260,000 iterations and a random 16-byte salt. Stored as `iterations$b64salt$b64hash`. On login the stored salt and iteration count are reused to recompute and compare in constant time. 260k iterations is the OWASP 2024 floor and is deliberately slow, which is correct for passwords.

**Account lockout.** Each failed login increments `failed_attempts`. At 5 failures the account is locked for 15 minutes by setting `locked_until`. A login against a locked account returns **429 Too Many Requests** (not 423). Counters reset on a successful login.

**Audit log.** A separate table records every login, failed login, blocked-login, logout, role change, and unlock, each with username, event, IP (X-Forwarded-For aware), detail, and timestamp. Readable only by admins via `GET /auth/audit`.

**Eight endpoints.** `register` (201), `login` (returns JWT), `me` (profile from DB, not just token claims), `logout` (200), `promote` (admin), `unlock` (admin), `users` (admin), `audit` (admin).

**Timing oracle defence.** A module-level `_DUMMY_HASH` is computed at startup. When a username does not exist, the code still runs a PBKDF2 comparison against the dummy hash, so the unknown-user path and the wrong-password path take the same time and both return an identical 401. This stops an attacker from learning which usernames exist by measuring response time.

**Admin self-registration blocked.** `register_user` takes `allow_admin=False` by default, and public `/register` never overrides it, so anyone registering through the API gets `analyst`. The `admin` role can only be granted by an existing admin through `/promote` (403 otherwise).

**Base64url padding fix.** `padding = (4 - len(s) % 4) % 4`. The outer `% 4` ensures that a string whose length is already a multiple of 4 gets zero padding instead of four spurious `=` characters, which would otherwise corrupt the decode.

**In-memory SQLite singleton for tests.** Using `file::memory:?cache=shared` with one held-open connection keeps a single in-memory database alive across test fixtures, instead of each new connection getting its own empty database and wiping state between calls.

---

## 5. Authorisation and the simulated-user reality

There are no pre-seeded "members." The user table starts empty. "Simulating users" means: you call `/auth/register` to create analyst accounts, then log in as them. That is a real auth system operating on a small, self-created user set, not a mock.

Two honest operational caveats:

- **First admin is a chicken-and-egg problem.** Public registration only creates analysts, and only an admin can promote. Out of the box there is no admin and no public way to create one. The first admin must be created by a one-off script that calls `register_user(..., allow_admin=True)` or by editing the database directly. There is no bootstrap path in the code.
- **Logout does not revoke anything.** JWTs are stateless and there is no blocklist. `/auth/logout` only writes an audit entry; the docstring says token invalidation is client-side. An issued token stays valid until its `exp` (default 1 hour) no matter how many times the user "logs out." If a token leaks, it is usable until it expires.

---

## 6. Honest quality assessment

The words "completely secure," "enterprise," and "best performance" do not survive contact with the code. Here is the calibrated version, which is more useful for a credible review anyway.

### What is genuinely strong
- Password handling is correct and modern: PBKDF2 260k, per-user salt, constant-time compare, timing-equalised unknown-user path.
- JWTs are verified properly: signature and expiry both checked, constant-time signature compare.
- Lockout, user-enumeration defence, and admin-escalation blocking are real and work.
- Enforcement is structural (router-level), so routes cannot silently ship unguarded.
- There is a real audit trail.

### Real limitations (the gap to "enterprise")
- **No token revocation.** Stateless JWT with no blocklist or refresh-token rotation. This is the headline auth weakness.
- **Symmetric signing (HS256).** The signing key is also the verification key. Anyone who holds `OIL_SECRET_KEY` can mint valid admin tokens. Multi-service setups usually want asymmetric (RS256/ES256).
- **Secret-key fragility.** If `OIL_SECRET_KEY` is unset, a random key is generated per process, so tokens break on restart and across instances. It must be set as a managed secret.
- **No rate limiting beyond per-account lockout.** Nothing throttles registration spam or brute force spread across many accounts or IPs.
- **No MFA, no email verification, no password reset, no password breach check.** Minimum is 8 characters with no complexity policy.
- **SQLite, single file, single shared connection.** Fine for low volume, not for concurrent writes or horizontal scale. No encryption at rest.
- **Two-role RBAC, no object-level authorisation.** No per-tenant or per-resource ownership. Acceptable because the data is shared public reference data, but it is not multi-tenant.
- **Single instance, in-process state.** The graph is cached and mutated in process. Each worker has its own copy, so horizontal scaling means duplicated state and per-process caches, not shared state.
- **Coverage gaps.** Lockout, duplicate-registration, and audit population are implemented but not each covered by a named test.

### Reliability and robustness
- Reasonable: 121 passing tests, a real integration test against the wired app, input validation on auth endpoints (length checks, role validation), graceful MISP-optional startup.
- Weak spots: no health of the background scheduler surfaced, no structured logging or metrics, no retry/circuit-breaker on outbound feed calls visible in the live path, single point of failure (one instance, one SQLite file).

### Performance, and what the cleanup actually did
- The dead-code and dependency cleanup did **not** make requests faster. Dead code was not executing. What it improved: a smaller Docker image and faster cold starts and deploys (four heavy libraries removed), a smaller dependency attack surface, and lower maintenance load. Calling it a runtime optimisation would be inaccurate.
- The graph is tiny (about 37 nodes) and loaded once, so intelligence reads are effectively instant.
- The real CPU cost is login: PBKDF2 at 260k iterations is intentionally tens of milliseconds of CPU per attempt, so a burst of concurrent logins is CPU-bound. That is a correct tradeoff, but it is the thing that would bottleneck first under load.

### What "enterprise-grade" would actually require
SSO/OIDC, MFA, refresh tokens with revocation, scoped RBAC with orgs/tenants, rate limiting and a WAF, a managed database (Postgres) with encryption at rest, a secrets manager with key rotation, structured logging plus metrics and tracing, audit-log shipping to a SIEM, and an external penetration test. None of this is present, and none of it needs to be for an alpha research platform. The point is to not claim it.

---

## 7. The frontend gap and a brand direction

**The factual problem.** `index.html` calls the intelligence endpoints with no `Authorization` header and has no login flow, no token storage, and no auth UI. After v0.7.0 it is broken against the secured backend. So the answer to "auth has no representation in the frontend" is: it has none, and the lack is now a functional failure, not a cosmetic one.

**What it already has.** A genuine dark "intelligence console" identity exists: a dark base, neon accents defined as CSS variables (`--purple #a855f7`, `--green #00e5a0`, `--amber #f5a623`, `--red #ff4444`, `--text #c8d8f0`), a starfield, a topbar with live API/MISP status pills and a clock, a sidebar with search and type filters, a graph/table/campaigns/attack tab set, and a detail panel. It is not a blank slate.

**Likely dead or non-functional UI.** The campaigns tab has no data source: there is no `/intelligence/campaigns` endpoint and campaigns are not in the live graph. So that tab is probably empty or static. Worth verifying and either wiring or hiding.

**A coherent direction (to be built, not yet built).**
- Make auth a first-class part of the dashboard: a session indicator in the topbar (logged-in user, role badge, token expiry countdown), a login gate or redirect to `/ui/auth.html` when calls return 401, token stored in memory and attached as a Bearer header to every fetch, and an auth-aware "graceful degraded" state instead of a blank graph.
- Brand identity for an intelligence product: lean into the existing dark + neon scheme but make it intentional. A risk-driven palette (calm teal/green for low, amber for elevated, red for critical) ties color to meaning, which is good design psychology for a risk tool: color should encode severity, not just decorate. Role should be visually distinct (analyst vs admin badge). The admin surface should feel different from the analyst surface.
- Remove or wire the non-functional tab, replace any placeholder controls with real ones, and make the API probe panel an authenticated diagnostic rather than an open one.

This is a real piece of work, not a tweak, and it is the natural next deliverable.

---

## 8. Forward look: agentic users (future, with caveats)

The idea of bots that authenticate and act on a user's behalf (for example, an agent doing legal paperwork) is interesting but introduces a different security model than human login:

- **Machine identity, not passwords.** Agents should use service accounts with API keys or OAuth client-credentials, not username and password with a 1-hour human JWT. Long-running agents need token rotation, not re-typing a password.
- **Least privilege and scopes.** A bot should hold narrow, explicit scopes (for example, "read entities," "submit form X"), not blanket analyst or admin. The current two-role model is too coarse for this.
- **Non-repudiation and audit.** Every agent action needs to be attributable to both the agent and the human principal it acts for. The existing audit log is a start but would need an "on behalf of" dimension.
- **Authorisation to act, and liability.** An agent performing legal paperwork raises questions far beyond authentication: who is legally responsible, what is the agent authorised to sign, how is consent captured and revoked, and what regulatory regime applies. These are product and legal questions, and they dwarf the auth implementation.

Short version: the current system can authenticate a human analyst well. Authenticating autonomous agents that take legally meaningful actions is a separate design with its own identity model, scoping, audit, and compliance work. Good direction for a future version, not a small addition.
