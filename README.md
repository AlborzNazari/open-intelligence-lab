# Open Intelligence Lab

[![Research Status](https://img.shields.io/badge/research-alpha-blue)](https://github.com/AlborzNazari/open-intelligence-lab)
[![Dataset Version](https://img.shields.io/badge/datasets-v0.1-green)](https://github.com/AlborzNazari/open-intelligence-lab/tree/main/datasets)
[![Model Version](https://img.shields.io/badge/intelligence_model-v0.7-orange)](https://github.com/AlborzNazari/open-intelligence-lab)
[![CI/CD](https://img.shields.io/badge/CI%2FCD-GitLab%20Pipeline-fc6d26)](https://gitlab.com/alborznazari4/open-intelligence-lab/-/pipelines)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![MITRE ATT&CK](https://img.shields.io/badge/MITRE-ATT%26CK%20Aligned-red)](https://attack.mitre.org/)
[![STIX 2.1](https://img.shields.io/badge/STIX-2.1%20Compliant-8b5cf6)](https://oasis-open.github.io/cti-documentation/stix/intro)
[![TAXII 2.1](https://img.shields.io/badge/TAXII-2.1%20Server-7c3aed)](https://docs.oasis-open.org/cti/taxii/v2.1/os/taxii-v2.1-os.html)
[![MISP](https://img.shields.io/badge/MISP-Integrated-6d28d9)](https://www.misp-project.org/)
[![Deployed on Fly.io](https://img.shields.io/badge/deployed-Fly.io-8B5CF6?logo=flydotio&logoColor=white)](https://open-intelligence-lab-cyrmjw.fly.dev)
[![Tests](https://img.shields.io/badge/tests-121%20passed-brightgreen)](https://gitlab.com/alborznazari4/open-intelligence-lab/-/pipelines)

<img width="1237" height="596" alt="Sleeze_Slither" src="https://github.com/user-attachments/assets/8fde77d8-9d33-4365-9453-c35cbda7eb96" />

**Open Intelligence Lab** is an ethical OSINT research platform focused on public-security intelligence representation, graph-based threat modeling, and explainable risk analytics.

It provides a clean, modular environment for researchers, analysts, and engineers who want to explore open-source intelligence signals without compromising privacy or ethics, using only public data, with every risk score backed by an interpretable rationale.

As of **v0.7.0**, the platform includes a full user authentication and authorisation system: JWT-based identity, PBKDF2 password hashing, role-based access control (analyst / admin), account lockout, and a server-side audit log recording every login, failure, promotion, and logout with IP address and timestamp. Authentication is enforced at the router level, so every intelligence endpoint requires a valid token.

**How the Software Works**
> Read the v0.5.0 article: [jump to Pipeline Architecture](https://medium.com/@alborznazari4/open-intelligence-lab-v0-5-0-from-research-platform-to-production-ci-cd-pipeline-4fb56cd21cd7)

> Read the full article: [From a Black Box to a Transparent, Modular, and Open-Source Model](https://medium.com/@alborznazari4/open-intelligence-lab-on-git-from-a-black-box-to-a-transparent-modular-and-open-source-model-ffa154962964)

**Visual Lab**
Open Intelligence Lab is fully live from v0.5.0. Fly.io hosts the backend 24/7, no local uvicorn needed.
> Explore the live graph: [alborznazari.github.io/open-intelligence-lab](https://alborznazari.github.io/open-intelligence-lab/)
> Secure access portal: [open-intelligence-lab-cyrmjw.fly.dev/ui/auth.html](https://open-intelligence-lab-cyrmjw.fly.dev/ui/auth.html)


## What Does This Software Do?

Open Intelligence Lab models real-world threat intelligence as a **traversable knowledge graph**:

- **22 entities**: threat actors (APT28, APT29, APT41, Lazarus, LockBit, Cl0p, KillNet), 8 malware families, 2 CVEs, 2 infrastructure nodes, and 3 target sectors
- **15 attack patterns** loaded as graph nodes and mapped to MITRE ATT&CK technique IDs
- **28 documented relations**: `uses`, `exploits`, `targets`, `uses_pattern`, `related_to`
- **7 documented campaigns** in the dataset (Operation Fancy Bear, Operation SolarWinds / SUNBURST, Operation Double Dragon, Operation AppleJeus, LockBit Global Ransomware, Operation MOVEit Mass Exploitation, KillNet NATO DDoS), exported via STIX
- **Risk scoring**: every entity gets a score from 0.0 to 1.0 derived from its base risk and graph degree (structural connectivity), bucketed into `LOW / MEDIUM / HIGH / CRITICAL`
- **Explainability**: every risk score produces a plain-language rationale, never a naked number
- **MITRE ATT&CK alignment**: all actors and patterns are mapped to official technique IDs
- **STIX 2.1 export** *(v0.3.0)*: full bundle export for Splunk, Sentinel, OpenCTI, and QRadar
- **TAXII 2.1 server** *(v0.3.0)*: live feed endpoint that threat platforms can poll directly
- **MISP live feed + TAXII ingestion** *(v0.4.0)*: pull intelligence from external sources with provenance validation
- **Docker support** *(v0.4.0)*: single `docker compose up` spins up the full stack including a local MISP instance
- **GitLab CI/CD pipeline** *(v0.5.0)*: 5-stage pipeline with lint, tests, Docker build, security scanning, and manual deploy gate
- **121-test pytest suite** *(v0.7.0)*: coverage across graph engine, risk analyzer, explainer, service layer, HTTP endpoints, user auth, and a real-app auth integration test
- **User authentication and authorisation** *(v0.7.0)*: JWT, PBKDF2, role enforcement, lockout, audit log


## Repository Architecture

```
open-intelligence-lab/
├── demo.py                        ← Entry point — runs the full pipeline
├── index.html                     ← Visual Lab (GitHub Pages)
├── auth.html                      ← v0.7.0 — Secure access portal (login/register/admin)
├── Dockerfile                     ← v0.4.0 / v0.6.0 — OCI labels, non-root user, healthcheck
├── docker-compose.yml             ← v0.4.0 — Full stack: OI Lab + MISP instance
├── .gitlab-ci.yml                 ← v0.5.0 / v0.6.0 — 5-stage pipeline, real flyctl deploy
├── requirements.txt               ← Runtime dependencies (fastapi, uvicorn, networkx)
├── requirements-dev.txt           ← v0.6.0 — CI/test dependencies
├── fly.toml                       ← v0.5.0 / v0.6.0 — Fly.io config
├── wrangler.jsonc                 ← v0.5.0 — Cloudflare Workers config (deploys ./visualization)
│
├── scripts/
│   ├── validate_schemas.py
│   └── smoke_test.py
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                ← v0.7.0 — pins auth env before import (deterministic suite)
│   ├── test_placeholder.py
│   ├── test_graph_builder.py
│   ├── test_risk_analyzer.py
│   ├── test_intelligence_explainer.py
│   ├── test_service.py
│   ├── test_api_endpoints.py
│   ├── test_user_auth.py          ← v0.7.0 — 7 auth unit tests (JWT, lockout, role enforcement)
│   └── test_app_auth_integration.py ← v0.7.0 — 4 tests against the real app (auth wiring proof)
│
├── datasets/
│   ├── threat_entities.json
│   ├── attack_patterns.json
│   ├── relations.json
│   ├── campaigns.json
│   └── mitre_mapping.json
│
├── core_engine/
│   ├── graph_builder.py
│   ├── risk_analyzer.py
│   ├── intelligence_explainer.py
│   └── intelligence_entities.py
│
├── visualization/
│   └── .gitkeep                   ← Cloudflare deploy target; demo.py generates dashboard.html here
│
├── api/
│   ├── main.py                    ← v0.7.0 — auth router wired, intelligence routes guarded, static files served
│   └── intelligence/
│       ├── router.py
│       └── service.py
│
└── backend/
    ├── auth.py                    ← v0.7.0 — JWT, PBKDF2, lockout, audit log, role enforcement
    ├── auth_router.py             ← v0.7.0 — /auth endpoints (register, login, me, promote, audit)
    ├── stix_exporter.py
    ├── taxii_server.py
    ├── misp_client.py
    ├── taxii_ingestor.py
    ├── feed_scheduler.py
    └── provenance.py
```

> Note: `exports/` (STIX output) and `visualization/dashboard.html` are generated at runtime and git-ignored, so they are not tracked in the repo.

<img width="928" height="916" alt="Medium_02" src="https://github.com/user-attachments/assets/769d41e7-2bca-4b4b-978b-01c58a1e095b" />


## Quick Start

### Option A: Python (static data, no Docker required)

```bash
git clone https://github.com/AlborzNazari/open-intelligence-lab.git
cd open-intelligence-lab
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn api.main:app --reload --port 8000
```

- **Interactive docs:** http://localhost:8000/docs
- **Health check:** http://localhost:8000/health
- **Auth portal:** http://localhost:8000/ui/auth.html

Every `/intelligence/*` endpoint requires a token, so register and log in at the auth portal (or `POST /auth/register` then `POST /auth/login`) and send the returned JWT as a `Bearer` token.

### Option B: Docker

```bash
docker compose up
```

---

## v0.7.0: User Authentication and Authorisation

v0.7.0 adds a production-grade identity and access management layer, and wires it into the running application so every intelligence route is authenticated. The auth system is built entirely on the Python standard library, no PyJWT, no bcrypt, no additional dependencies.

### Architecture

```
POST /auth/register   →  creates analyst account (full name stored server-side)
POST /auth/login      →  returns signed JWT, records login + IP in audit log
GET  /auth/me         →  returns full profile from DB (not just token claims)
POST /auth/logout     →  records logout event in audit log
POST /auth/promote    →  admin only — change any user's role
POST /auth/unlock     →  admin only — clear account lockout
GET  /auth/users      →  admin only — all users with metadata
GET  /auth/audit      →  admin only — last 100 audit events
```

### Security Properties

| Property | Implementation |
|---|---|
| Password storage | PBKDF2-HMAC-SHA256, 260,000 iterations (OWASP 2024), random 16-byte salt per user |
| Token format | HS256 JWT: `sub`, `role`, `name`, `iat`, `exp`, clean-room implementation |
| Timing oracle defence | Constant-time PBKDF2 on both "wrong password" and "user not found" paths |
| User enumeration defence | Both failure cases return identical 401 with identical message |
| Account lockout | 5 consecutive failures → 15-minute lock (configurable via env vars) |
| Privilege escalation prevention | Public `/register` always creates `analyst`; `admin` role only assignable by existing admin via `/promote` |
| Audit log | Every login, failure, lockout, logout, role change, and unlock recorded with timestamp + IP |
| Role enforcement | `require_role(...)` dependency factory, declared on the route or router, not scattered `if` checks |

### User Schema

```sql
CREATE TABLE users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    username        TEXT    UNIQUE NOT NULL,
    full_name       TEXT    NOT NULL DEFAULT '',
    password        TEXT    NOT NULL,           -- PBKDF2: iterations$b64salt$b64hash
    role            TEXT    NOT NULL DEFAULT 'analyst',
    created         INTEGER NOT NULL,           -- Unix timestamp
    last_login      INTEGER,                    -- Unix timestamp
    last_login_ip   TEXT,                       -- X-Forwarded-For aware
    failed_attempts INTEGER NOT NULL DEFAULT 0,
    locked_until    INTEGER NOT NULL DEFAULT 0
);
```

### Protecting Routes

Enforcement is applied once at the router level, so no individual route can ship unguarded:

```python
from fastapi import Depends
from backend.auth import require_role

# In api/main.py — every intelligence route requires analyst or admin:
app.include_router(
    intelligence_router,
    dependencies=[Depends(require_role("analyst", "admin"))],
)
```

The same dependency factory can guard a single route when you need a stricter role:

```python
from backend.auth import get_current_user, require_role

@app.get("/example/any-user")
def any_user(claims: dict = Depends(get_current_user)):
    ...

@app.post("/example/admin-only")
def admin_only(claims: dict = Depends(require_role("admin"))):
    ...
```

### Auth UI

`auth.html` at `/ui/auth.html` provides a complete frontend:
- Register form with full name, username, password
- Login with auto-session restore on page reload
- Identity card showing full name, role badge, last login time, last login IP, session expiry
- Bearer token preview with copy button
- Admin panel (visible to admin role only): full user table with role management, account unlock, and live audit log

### Environment Variables

| Variable | Default | Description |
|---|---|---|
| `OIL_SECRET_KEY` | random hex | JWT signing secret. **Set this in production**, or tokens reset on every restart |
| `OIL_TOKEN_TTL` | `3600` | Token lifetime in seconds |
| `OIL_USER_DB` | `oil_users.db` | SQLite database path (keep this out of version control) |
| `OIL_MAX_ATTEMPTS` | `5` | Failed logins before lockout |
| `OIL_LOCKOUT_SEC` | `900` | Lockout duration in seconds (15 min) |

---

## Test Suite: 121 Tests, 0 Failures

Run from the repo root with `pytest tests/`.

| File | Tests | What it covers |
|---|---|---|
| `test_graph_builder.py` | 15 | Dataset loading, node/edge integrity, known entity IDs, attribute types, risk score range `[0,1]`, APT28→X-Agent edge, no self-loops |
| `test_risk_analyzer.py` | 8 | Score computation, capping at `1.0`, write-back to graph nodes, isolated-node base preservation |
| `test_intelligence_explainer.py` | 14 | Response shape, type-specific content, all four verdict labels |
| `test_service.py` | 31 | Service functions, every filter combination, pagination, sort order |
| `test_api_endpoints.py` | 41 | All HTTP routes via TestClient (authenticated), 404 and 422 error paths included |
| `test_user_auth.py` | 7 | Registration with full name, JWT claim integrity, wrong password → 401, user enumeration defence, `/me` full profile, analyst → 403 on admin routes, expired token rejection |
| `test_app_auth_integration.py` | 4 | Auth wired into the real app: `/auth` mounted, no token → 401, valid token → 200, forged token rejected |
| `test_placeholder.py` | 1 | Suite smoke check |

---

## Risk Model

```
Risk Score = base_risk + degree_factor
```

`degree_factor` is the entity's graph degree divided by 10, so more relationships raise risk. The result is clamped to `[0.0, 1.0]` and bucketed:

| Band | Score Range |
|------|------------|
| CRITICAL | ≥ 0.90 |
| HIGH | ≥ 0.70 |
| MEDIUM | ≥ 0.40 |
| LOW | < 0.40 |

---

## Roadmap

| Version | Focus | Status |
|---|---|---|
| **v0.1.0** | Core graph engine, datasets, API, Visual Lab | Complete |
| **v0.2.0** | FastAPI backend live; full-stack connected | Complete |
| **v0.3.0** | STIX 2.1 export, TAXII 2.1 server, platform interop | Complete |
| **v0.4.0** | MISP integration, TAXII ingestion, provenance, Docker | Complete |
| **v0.5.0** | GitLab CI/CD pipeline, Docker build, security scanning | Complete |
| **v0.6.0** | pytest suite, flyctl deploy, Docker hardening | Complete |
| **v0.7.0** | JWT auth wired in, PBKDF2, role enforcement, lockout, audit log, auth UI, repo cleanup | Complete |
| **v1.0.0** | Neo4j backend, multi-hop actor pivoting, ML scoring with SHAP | Planned |

---

## Core Principles

- **Public data only**: no private, scraped, or sensitive information
- **Explainability first**: every risk score must be traceable and expressible in plain language
- **Modular architecture**: each layer can be replaced or extended independently
- **Research transparency**: datasets, scoring logic, and relationships are fully visible
- **Ethical OSINT**: aligned with academic norms and MITRE ATT&CK attribution standards
- **Standard-first interoperability**: STIX 2.1 / TAXII 2.1 compliance ensures plug-and-play integration

---

## Contributing

Contributions are welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md) and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before submitting a pull request.

---

*Open Intelligence Lab · Alborz Nazari · 2026 · [medium.com/@alborznazari4](https://medium.com/@alborznazari4)*

## License

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/AlborzNazari/open-intelligence-lab/blob/main/LICENSE)