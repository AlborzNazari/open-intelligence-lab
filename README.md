# Open Intelligence Lab

[![Research Status](https://img.shields.io/badge/research-alpha-blue)](https://github.com/AlborzNazari/open-intelligence-lab)
[![Dataset Version](https://img.shields.io/badge/datasets-v0.1-green)](https://github.com/AlborzNazari/open-intelligence-lab/tree/main/datasets)
[![Model Version](https://img.shields.io/badge/intelligence_model-v0.6-orange)](https://github.com/AlborzNazari/open-intelligence-lab)
[![CI/CD](https://img.shields.io/badge/CI%2FCD-GitLab%20Pipeline-fc6d26)](https://gitlab.com/alborznazari4/open-intelligence-lab/-/pipelines)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![MITRE ATT&CK](https://img.shields.io/badge/MITRE-ATT%26CK%20Aligned-red)](https://attack.mitre.org/)
[![STIX 2.1](https://img.shields.io/badge/STIX-2.1%20Compliant-8b5cf6)](https://oasis-open.github.io/cti-documentation/stix/intro)
[![TAXII 2.1](https://img.shields.io/badge/TAXII-2.1%20Server-7c3aed)](https://docs.oasis-open.org/cti/taxii/v2.1/os/taxii-v2.1-os.html)
[![MISP](https://img.shields.io/badge/MISP-Integrated-6d28d9)](https://www.misp-project.org/)
[![GitLab CI/CD](https://img.shields.io/badge/GitLab-Pipeline-fc6d26?logo=gitlab)](https://gitlab.com/alborznazari4/open-intelligence-lab/-/pipelines)
[![Deployed on Fly.io](https://img.shields.io/badge/deployed-Fly.io-8B5CF6?logo=flydotio&logoColor=white)](https://open-intelligence-lab-cyrmjw.fly.dev)
[![Tests](https://img.shields.io/badge/tests-109%20passed-brightgreen)](https://gitlab.com/alborznazari4/open-intelligence-lab/-/pipelines)

<img width="1237" height="596" alt="Sleeze_Slither" src="https://github.com/user-attachments/assets/8fde77d8-9d33-4365-9453-c35cbda7eb96" />

**Open Intelligence Lab** is an ethical OSINT research platform focused on public-security intelligence representation, graph-based threat modeling, and explainable risk analytics..

It provides a clean, modular environment for researchers, analysts, and engineers who want to explore open-source intelligence signals **without compromising privacy or ethics** — using only public data, with every risk score backed by an interpretable rationale.

As of **v0.4.0**, the platform is fully interoperable with Splunk Enterprise Security, Microsoft Sentinel, OpenCTI, and IBM QRadar via STIX 2.1 exports and a built-in TAXII 2.1 server — and now includes live MISP feed ingestion, a TAXII 2.1 client, and provenance-validated chain-of-custody for every ingested intelligence object.

**How the Software Works**
> 📖 Read the v0.5.0 article — [jump to Pipeline Architecture](https://medium.com/@alborznazari4/open-intelligence-lab-v0-5-0-from-research-platform-to-production-ci-cd-pipeline-4fb56cd21cd7)

> 📖 Read the full article: [From a Black Box to a Transparent, Modular, and Open-Source Model](https://medium.com/@alborznazari4/open-intelligence-lab-on-git-from-a-black-box-to-a-transparent-modular-and-open-source-model-ffa154962964)

**Visual Lab**
Open Intelligence Lab is fully live from v0.5.0!
Fly.io hosts the backend on a server 24/7, so it no longer needs to be run locally via uvicorn: it has become a platform-independent, internet-facing service using PaaS.
Just click on Probe backend. All data will turn live.
> 🔬 Explore the live graph: [alborznazari.github.io/open-intelligence-lab](https://alborznazari.github.io/open-intelligence-lab/)


## What Does This Software Do?

Open Intelligence Lab models real-world threat intelligence as a **traversable knowledge graph** -->

- **22 entities** — threat actors (APT28, APT29, APT41, Lazarus, LockBit, Cl0p, KillNet), 8 malware families, 2 CVEs, 2 infrastructure nodes, and 3 target sectors
- **28 documented relations** — `uses`, `exploits`, `targets`, `uses_pattern`, `related_to`
- **7 real campaigns** — Operation Fancy Bear, Operation SolarWinds (SUNBURST), Operation Double Dragon, Operation AppleJeus, LockBit Global Ransomware, Operation MOVEit Mass Exploitation, KillNet NATO DDoS
- **Risk scoring** — every entity gets a score from 0.0 to 1.0 derived from its base risk, graph degree (structural connectivity), and incident neighbor weighting, bucketed into `LOW / MEDIUM / HIGH / CRITICAL`
- **Explainability** — every risk score produces a plain-language rationale, never a naked number
- **MITRE ATT&CK alignment** — all actors and patterns are mapped to official technique IDs
- **STIX 2.1 export** *(v0.3.0)* — full bundle export for Splunk, Sentinel, OpenCTI, and QRadar
- **TAXII 2.1 server** *(v0.3.0)* — live feed endpoint that threat platforms can poll directly
- **MISP live feed + TAXII ingestion** *(v0.4.0)* — pull intelligence from external sources with provenance validation
- **Docker support** *(v0.4.0)* — single `docker compose up` spins up the full stack including a local MISP instance
- **GitLab CI/CD pipeline** *(v0.5.0)* — 5-stage pipeline with lint, tests, Docker build, security scanning, and manual deploy gate
- **109-test pytest suite** *(v0.6.0)* — full coverage across graph engine, risk analyzer, explainer, service layer, and all HTTP endpoints

Run `demo.py` and an **interactive browser dashboard** opens showing the full threat knowledge graph — click any node to inspect its risk score, confidence, connections, and intelligence rationale.


## Repository Architecture

```
open-intelligence-lab/
├── demo.py                        ← Entry point — runs the full pipeline
├── index.html                     ← Visual Lab (GitHub Pages)
├── Dockerfile                     ← ★ v0.4.0 / v0.6.0 — OCI labels, non-root user, fixed healthcheck
├── docker-compose.yml             ← ★ v0.4.0 — Full stack: OI Lab + MISP instance
├── .gitlab-ci.yml                 ← ★ v0.5.0 / v0.6.0 — 5-stage pipeline, real flyctl deploy
├── requirements.txt               ← Runtime dependencies
├── requirements-dev.txt           ← ★ v0.6.0 — CI/test dependencies (pytest, httpx, flake8...)
├── fly.toml                       ← ★ v0.5.0 / v0.6.0 — Fly.io config, memory conflict fixed
├── wrangler.jsonc                 ← ★ v0.5.0 — Cloudflare Workers scoped to visualization/
│
├── scripts/                       ← CI helper scripts
│   ├── validate_schemas.py        ← ★ v0.6.0 — Fixed paths, covers all 5 datasets
│   └── smoke_test.py              ← ★ v0.6.0 — Retry loop, 8 endpoint tests
│
├── tests/                         ← ★ v0.6.0 — Full pytest suite (109 tests, 0 failures)
│   ├── __init__.py
│   ├── test_placeholder.py        ← v0.5.0 placeholder (kept)
│   ├── test_graph_builder.py      ← ★ v0.6.0 — 15 tests: graph loading + integrity
│   ├── test_risk_analyzer.py      ← ★ v0.6.0 — 8 tests: scoring logic + edge cases
│   ├── test_intelligence_explainer.py  ← ★ v0.6.0 — 14 tests: explanation structure + verdicts
│   ├── test_service.py            ← ★ v0.6.0 — 27 tests: all service functions + filters
│   └── test_api_endpoints.py      ← ★ v0.6.0 — 44 HTTP tests via TestClient
│
├── datasets/                      ← 5 JSON knowledge base files
│   ├── threat_entities.json       ← 22 entities (actors, malware, CVEs, sectors, infra)
│   ├── attack_patterns.json       ← 15 OSINT attack patterns with MITRE mappings
│   ├── relations.json             ← 28 directed edges (the graph lives here)
│   ├── campaigns.json             ← 7 real-world campaigns (Diamond Model)
│   └── mitre_mapping.json         ← ATT&CK technique profiles per actor
│
├── core_engine/                   ← Intelligence pipeline
│   ├── graph_builder.py           ← Builds DiGraph from datasets (NetworkX)
│   ├── risk_analyzer.py           ← Risk = base + degree_factor + incident_factor
│   ├── intelligence_explainer.py  ← Plain-language rationale generator
│   └── intelligence_entities.py  ← Entity data model
│
├── visualization/
│   └── graph_renderer.py          ← Interactive browser graph (Canvas + D3-style)
│
├── api/
│   ├── main.py                    ← ★ v0.6.0 — v0.6.0, CORS + fly.dev origin added
│   └── intelligence/
│       ├── router.py              ← GET /intelligence/analyze/{entity_id}
│       ├── service.py             ← Pipeline orchestration
│       └── schemas.py            ← Pydantic response models
│
├── backend/
│   ├── stix_exporter.py           ← ★ v0.3.0 — STIX 2.1 bundle builder + platform exporters
│   ├── taxii_server.py            ← ★ v0.3.0 / v0.4.0 — TAXII 2.1 server
│   ├── misp_client.py             ← ★ v0.4.0 — MISP REST API client + STIX normalization
│   ├── taxii_ingestor.py          ← ★ v0.4.0 — TAXII 2.1 feed subscriber
│   ├── feed_scheduler.py          ← ★ v0.4.0 — Ingestion orchestrator + live object store
│   ├── provenance.py              ← ★ v0.4.0 — Chain-of-custody engine + trust scoring
│   └── requirements.txt          ← Backend/server reference dependencies
│
└── exports/                       ← ★ v0.3.0 — Generated STIX export files (git-ignored)
    ├── stix_bundle.json
    ├── splunk_events.json
    ├── sentinel_indicators.json
    ├── opencti_bundle.json
    ├── qradar_objects.json
    └── export_summary.json
```

<img width="928" height="916" alt="Medium_02" src="https://github.com/user-attachments/assets/769d41e7-2bca-4b4b-978b-01c58a1e095b" />


## Quick Start

### Not Necessary. For engineers & enthusiasts who use python or uvicorn app to run the app instead of PaaS Visual Lab host server.

There are Two ways to run the project:

### Option A — Python (static data, no Docker required)

#### Prerequisites

- **Python 3.10+** — [python.org/downloads](https://www.python.org/downloads/)
- **Git** — [git-scm.com](https://git-scm.com/)

Verify:
```bash
python --version   # must be 3.10+
git --version
```

#### 1 — Clone

```bash
git clone https://github.com/AlborzNazari/open-intelligence-lab.git
cd open-intelligence-lab
```

#### 2 — Create Virtual Environment

```bash
python -m venv venv
```

Activate:

| Platform | Command |
|----------|---------|
| Windows (PowerShell) | `venv\Scripts\Activate.ps1` |
| Windows (CMD) | `venv\Scripts\activate.bat` |
| macOS / Linux | `source venv/bin/activate` |

You should see `(venv)` at the start of your prompt.

> **Windows note:** If you get a script execution error, run this first:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

#### 3 — Install Dependencies

```bash
pip install -r requirements.txt
```

> **Important:** Only install from the root `requirements.txt`. Do not run `pip install -r backend/requirements.txt` — that file pins older versions for reference only and will conflict on Python 3.12+.

> **Windows note:** If any package fails to build from source, use:
> ```bash
> pip install -r requirements.txt --only-binary=:all:
> ```

#### 4 — Run the Visual Lab

Open `index.html` directly in your browser for the full interactive graph.

#### 5 — Run the API

```bash
python -m uvicorn api.main:app --reload --port 8000
```

- **Interactive docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health check:** [http://localhost:8000/health](http://localhost:8000/health)

#### 6 — Run the Demo Pipeline

```bash
python demo.py
```

Your browser opens automatically with the interactive threat knowledge graph. In the terminal you will see the full risk analysis report printed for all entities.

---

### Option B — Docker (full stack with live MISP)

#### Prerequisites

- **Docker Desktop** — [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop/)
- **Git** — [git-scm.com](https://git-scm.com/)

#### 1 — Clone

```bash
git clone https://github.com/AlborzNazari/open-intelligence-lab.git
cd open-intelligence-lab
```

#### 2 — Start the Full Stack

```bash
docker compose up
```

This spins up two services:
- **OI Lab API** at `http://localhost:8000` — the FastAPI backend
- **MISP** at `https://localhost` — a full local MISP instance

MISP takes ~2 minutes to initialize on first boot.

#### 3 — Get Your MISP API Key

1. Open `https://localhost` in your browser (accept the self-signed cert warning)
2. Login: `admin@admin.test` / `admin`
3. Top-right corner → click your username → **My Profile**
4. Scroll down to **Auth key** → copy it

#### 4 — Connect OI Lab to MISP

Stop compose (`Ctrl+C`), then restart with your key:

```bash
MISP_KEY=your-copied-key docker compose up
```

Or create a `.env` file in the project root:
```
MISP_KEY=your-copied-key
```

Then just run `docker compose up`. The OI Lab API will connect to MISP automatically on startup and begin pulling live threat intelligence every hour.

#### 5 — Open the Visual Lab

Open `index.html` in your browser and point the API URL to `http://localhost:8000`.

> **No MISP needed:** If you only want the containerized API without live feeds, skip steps 3–4. The app runs fully on static datasets without a MISP connection.

---

## Interactive Dashboard

When the API is running, open `index.html` in your browser:

| Feature | How |
|---------|-----|
| Zoom | Scroll wheel |
| Pan | Click and drag |
| Inspect entity | Click any node |
| Toggle labels | Click ⊞ button |
| Reset view | Click ⊙ button |

**Left panel** — full entity registry sorted by risk score
**Graph** — force-directed knowledge graph with all real threat actors, malware, CVEs, and sectors
**Right panel** — click any node to see its risk gauge, confidence, connection count, and plain-language explainability rationale
**Campaign panel** — all 7 documented campaigns with adversary and objective
**STIX Export panel** *(v0.3.0)* — per-platform export preview for Splunk, Sentinel, OpenCTI, and QRadar
**MISP Status panel** *(v0.4.0)* — live feed status, provenance chain state, TAXII ingestor readiness


## Running the API

```bash
python -m uvicorn api.main:app --reload --port 8000
```

If `uvicorn` is not found as a command:
```bash
pip install uvicorn fastapi
python -m uvicorn api.main:app --reload --port 8000
```

> **Always run from the project root** (`open-intelligence-lab/`), never from inside `api/`. The module path `api.main:app` requires the root as the working directory.

- **Interactive docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health check:** [http://localhost:8000/health](http://localhost:8000/health)
- **Analyze endpoint:** `http://localhost:8000/intelligence/analyze/{entity_id}`

Example:
```bash
curl http://localhost:8000/intelligence/analyze/TA-001
```


## Risk Model

```
Risk Score = base_risk + degree_factor + incident_factor
```

- `base_risk` — entity's baseline score from the dataset
- `degree_factor` — node's total connection count ÷ 10 (structural position in graph)
- `incident_factor` — count of connected `incident_category` nodes × 0.1

Clamped to `[0.0, 1.0]` and bucketed:

| Band | Score Range | Color |
|------|------------|-------|
| CRITICAL | ≥ 0.90 | 🔴 |
| HIGH | ≥ 0.70 | 🟠 |
| MEDIUM | ≥ 0.40 | 🟡 |
| LOW | < 0.40 | 🟢 |

Every score is accompanied by a plain-language rationale generated by `intelligence_explainer.py`. No risk score is ever a naked number.


## Datasets

All data is sourced from **public, ethical sources only**:

| File | Contents | Source |
|------|----------|--------|
| `threat_entities.json` | 22 entities across 5 types | MITRE ATT&CK, CISA Advisories |
| `attack_patterns.json` | 15 OSINT attack patterns | MITRE ATT&CK, public research |
| `relations.json` | 28 directed edges | MITRE ATT&CK, CISA, Mandiant |
| `campaigns.json` | 7 campaigns (Diamond Model) | Public threat reports |
| `mitre_mapping.json` | TTP profiles per actor | MITRE ATT&CK |


## v0.6.0 — Full Pytest Suite + Production CI/CD

v0.6.0 delivers the test coverage that was the stated goal of v0.5.1 and completes the CI/CD pipeline with a working Fly.io deployment step. Every previously stubbed or broken component now works end-to-end.

### Test Suite — 109 Tests, 0 Failures

| File | Tests | What it covers |
|---|---|---|
| `test_graph_builder.py` | 15 | Dataset loading, node/edge integrity, known entity IDs, attribute types, risk score range `[0,1]`, APT28→X-Agent edge, no self-loops |
| `test_risk_analyzer.py` | 8 | Score computation, capping at `1.0`, write-back to graph nodes, isolated-node base preservation, connectivity-based inflation |
| `test_intelligence_explainer.py` | 14 | Response shape, type-specific content (origin, malware type, CVSS), all four verdict labels (CRITICAL/HIGH/MODERATE/LOW) |
| `test_service.py` | 27 | All four service functions, every filter combination, pagination, sort order, 200-entity cap |
| `test_api_endpoints.py` | 44 | All 7 HTTP routes via Starlette `TestClient` — no live server — including 404 and 422 error paths |

Run the suite locally:

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

### What Else Changed in v0.6.0

| Component | Fix |
|---|---|
| `scripts/validate_schemas.py` | Was resolving `data/` (non-existent). Now resolves from `__file__` via `pathlib` — works from any CWD. Covers all 5 datasets. |
| `scripts/smoke_test.py` | `sleep 5` race condition replaced with a 10-attempt retry loop. Added 5 new endpoint tests. |
| `fly.toml` | `memory` and `memory_mb` were both set — lower value (256 MB) silently won. Fixed to `memory = '512mb'` only. |
| `Dockerfile` | `ARG VERSION`/`ARG GIT_SHA` were passed by CI but not declared in the file — OCI labels were empty. Fixed. Added non-root `appuser`. Healthcheck now targets `/health`. |
| `.gitlab-ci.yml` | `deploy_production` was a stub `echo`. Now installs flyctl and calls `flyctl deploy`. `rollback_production` validates `ROLLBACK_SHA` before proceeding. Added `PYTHONPATH` globally, Cobertura coverage report, Docker 26.1. |
| `.github/workflows/static.yml` | Pages deploy was ungated. Test job now gates it. Pip cache covers both requirements files. |
| `api/main.py` | Version bumped to `0.6.0`. `https://open-intelligence-lab-cyrmjw.fly.dev` added to CORS allowed origins. |
| `requirements-dev.txt` | New file — separates CI/test deps from runtime deps. Pip cache now invalidates correctly when dev deps change. |


## v0.5.0 — GitLab CI/CD Pipeline + Production Infrastructure

v0.5.0 operationalizes the platform. Every commit to main now goes through eight automated checks before a human decides to deploy.

### Pipeline — 5 Stages, 10 Jobs

| Stage | Jobs | Purpose |
|-------|------|---------|
| validate | `lint`, `schema_validate` | flake8/black/isort code quality. Dataset JSON validation on every commit. |
| test | `unit_tests`, `api_smoke_test` | pytest with coverage. Live FastAPI server spun up in CI — real endpoints, real datasets. |
| build | `build_docker`, `tag_release` | Docker image built with commit SHA tag, pushed to GitLab Container Registry. |
| security | `dependency_scan`, `container_scan` | pip-audit + safety on requirements.txt. Trivy scans image for HIGH/CRITICAL CVEs. |
| deploy | `deploy_production`, `rollback_production` | Manual-gate deploy to Fly.io. One-click rollback via `ROLLBACK_SHA` variable. |

### GitLab Pipeline
```
https://gitlab.com/alborznazari4/open-intelligence-lab/-/pipelines
```


## v0.3.0 — STIX 2.1 Interoperability

v0.3.0 adds full **STIX 2.1** compliance and a **TAXII 2.1** server that threat intelligence platforms can poll as a live feed.

### Entity → STIX Mapping

| OI Lab Entity Type | STIX 2.1 Object | Notes |
|---|---|---|
| `threat_actor` | `threat-actor` | Includes `x_oi_risk_score` extension |
| `malware` | `malware` | Capabilities and `is_family` fields populated |
| `infrastructure` | `infrastructure` | C2 nodes and exploit targets |
| `vulnerability` (CVE) | `vulnerability` | NVD external reference auto-linked |
| `sector` | `identity` (class: sector) | Victim sectors as STIX identity objects |
| `attack_pattern` | `attack-pattern` | Kill chain phases + MITRE external reference |
| `campaign` | `campaign` | Diamond Model fields as `x_oi_` extensions |
| Relations from `relations.json` | `relationship` | Directed, confidence-weighted |

### Platform Integration

| Platform | Method | Status |
|---|---|---|
| **Splunk Enterprise Security** | STIX-TAXII connector | ✅ Ready |
| **Microsoft Sentinel** | Threat Intelligence blade (TAXII) | ✅ Ready |
| **OpenCTI** | Native STIX 2.1 import or TAXII poll | ✅ Ready |
| **IBM QRadar SIEM** | STIX connector app | ✅ Ready |

### Running the STIX Export

```bash
python backend/stix_exporter.py
```

### Running the TAXII 2.1 Server

```bash
python -m uvicorn backend.taxii_server:app --host 0.0.0.0 --port 8000
```

| Endpoint | Description |
|---|---|
| `GET /taxii/` | Discovery |
| `GET /taxii/api-root/collections/` | Lists all collections |
| `GET /taxii/api-root/collections/{id}/objects/` | Returns STIX objects (paginated) |
| `GET /taxii/health` | Health check |

TAXII collections:

| Collection ID | Contents |
|---|---|
| `oi-lab-threat-actors-001` | Threat actor and identity objects |
| `oi-lab-attack-patterns-002` | MITRE-mapped attack patterns |
| `oi-lab-campaigns-003` | Diamond Model campaign objects |
| `oi-lab-full-bundle-004` | Complete STIX 2.1 bundle |


## v0.4.0 — Live Feed Ingestion + Provenance Validation

v0.4.0 adds the subscriber side: pulling live intelligence from external MISP instances and TAXII feeds, validating through a provenance engine, and merging into the knowledge graph.

### Activating the Live Feed

```bash
export MISP_URL=https://your-misp-instance.org
export MISP_KEY=your-api-key
python -m uvicorn api.main:app --reload --port 8000
```

| Variable | Default | Description |
|---|---|---|
| `MISP_LABEL` | `MISP-Live` | Human-readable feed label |
| `MISP_PULL_DAYS` | `7` | Days back to fetch per run |
| `MISP_LIMIT` | `200` | Max events per ingestion cycle |
| `MISP_VERIFY_SSL` | `true` | Set `false` for local Docker MISP |
| `MISP_INTERVAL_SECONDS` | `3600` | Ingestion interval in seconds |

### Provenance Validation

```
Source trust prior  ×  feed confidence  —  staleness penalty  =  adjusted trust level
```

| Source | Trust Prior |
|---|---|
| MISP-CISA | 1.00 |
| MISP-CERT-EU / MISP-CIRCL / MISP-NATO | 0.95 |
| MISP-Community | 0.75 |
| TAXII-OpenCTI | 0.85 |
| TAXII-Unknown | 0.60 |

Objects older than 90 days receive a −0.20 staleness penalty. Objects below 0.10 trust are rejected entirely.


## Core Principles

- **Public data only** — no private, scraped, or sensitive information
- **Explainability first** — every risk score must be traceable and expressible in plain language
- **Modular architecture** — each layer can be replaced or extended independently
- **Research transparency** — datasets, scoring logic, and relationships are fully visible
- **Ethical OSINT** — aligned with academic norms and MITRE ATT&CK attribution standards
- **Standard-first interoperability** — STIX 2.1 / TAXII 2.1 compliance ensures plug-and-play integration


## Roadmap

| Version | Focus | Status |
|---|---|---|
| **v0.1.0** | Core graph engine, datasets, API, Visual Lab | ✅ Complete |
| **v0.2.0** | FastAPI backend live; full-stack connected | ✅ Complete |
| **v0.3.0** | STIX 2.1 export, TAXII 2.1 server, Splunk / Sentinel / OpenCTI / QRadar interop | ✅ Complete |
| **v0.4.0** | MISP integration, TAXII feed ingestion, provenance validation, Docker support | ✅ Complete |
| **v0.5.0** | GitLab CI/CD pipeline, Docker build, security scanning, production deploy gate | ✅ Complete |
| **v0.6.0** | 109-test pytest suite, real flyctl deploy, Docker hardening, infra bug fixes | ✅ Complete |
| **v1.0.0** | Neo4j backend, multi-hop actor pivoting, ML scoring with SHAP explainability | 🗓 Planned |


## Contributing

Contributions are welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md) and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before submitting a pull request.


## Troubleshooting

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for the full guide covering:

- Windows two-Python problem and module not found errors
- Mixed content block (GitHub Pages HTTPS vs local HTTP API)
- Docker network issues and port conflicts
- MISP initialization and API key setup
- Caddy 502 errors


## How to Use MISP Data in the Visual Lab

Once MISP is connected and the live feed is active, the knowledge graph updates automatically every hour.

### Querying Ingested Data via the API

| Endpoint | What it returns |
|---|---|
| `GET /ingest/objects?source=MISP-Local` | All objects ingested from your local MISP |
| `GET /ingest/objects?min_trust=0.8` | Only high-confidence objects |
| `GET /ingest/run-log` | History of every ingestion cycle |
| `GET /ingest/store/summary` | Object count by type and source |
| `GET /ingest/bundle` | Full STIX 2.1 export of all ingested objects |

### Adding More Feeds

```bash
# Add another MISP instance
curl -X POST http://localhost:8000/ingest/misp \
  -H "Content-Type: application/json" \
  -d '{"label":"MISP-CIRCL","base_url":"https://misp.circl.lu","api_key":"your-key","pull_days":7}'

# Add a TAXII feed
curl -X POST http://localhost:8000/ingest/taxii \
  -H "Content-Type: application/json" \
  -d '{"label":"TAXII-OpenCTI","server_url":"https://your-opencti.org/taxii/","api_key":"your-key"}'
```


*Open Intelligence Lab · Alborz Nazari · 2026 · [medium.com/@alborznazari4](https://medium.com/@alborznazari4)*


## License

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/AlborzNazari/open-intelligence-lab/blob/main/LICENSE)
