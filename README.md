# Open Intelligence Lab

[![Research Status](https://img.shields.io/badge/research-alpha-blue)](https://github.com/AlborzNazari/open-intelligence-lab)
[![Dataset Version](https://img.shields.io/badge/datasets-v0.1-green)](https://github.com/AlborzNazari/open-intelligence-lab/tree/main/datasets)
[![Model Version](https://img.shields.io/badge/intelligence_model-v0.5-orange)](https://github.com/AlborzNazari/open-intelligence-lab)
[![CI/CD](https://img.shields.io/badge/CI%2FCD-GitLab%20Pipeline-fc6d26)](https://gitlab.com/alborznazari4/open-intelligence-lab/-/pipelines)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![MITRE ATT&CK](https://img.shields.io/badge/MITRE-ATT%26CK%20Aligned-red)](https://attack.mitre.org/)
[![STIX 2.1](https://img.shields.io/badge/STIX-2.1%20Compliant-8b5cf6)](https://oasis-open.github.io/cti-documentation/stix/intro)
[![TAXII 2.1](https://img.shields.io/badge/TAXII-2.1%20Server-7c3aed)](https://docs.oasis-open.org/cti/taxii/v2.1/os/taxii-v2.1-os.html)
[![MISP](https://img.shields.io/badge/MISP-Integrated-6d28d9)](https://www.misp-project.org/)
[![GitLab CI/CD](https://img.shields.io/badge/GitLab-Pipeline-fc6d26?logo=gitlab)](https://gitlab.com/alborznazari4/open-intelligence-lab/-/pipelines)

<img width="1237" height="596" alt="Sleeze_Slither" src="https://github.com/user-attachments/assets/8fde77d8-9d33-4365-9453-c35cbda7eb96" />

**Open Intelligence Lab** is an ethical OSINT research platform focused on public-security intelligence representation, graph-based threat modeling, and explainable risk analytics.

It provides a clean, modular environment for researchers, analysts, and engineers who want to explore open-source intelligence signals **without compromising privacy or ethics** — using only public data, with every risk score backed by an interpretable rationale.

As of **v0.4.0**, the platform is fully interoperable with Splunk Enterprise Security, Microsoft Sentinel, OpenCTI, and IBM QRadar via STIX 2.1 exports and a built-in TAXII 2.1 server — and now includes live MISP feed ingestion, a TAXII 2.1 client, and provenance-validated chain-of-custody for every ingested intelligence object.

**How the Software Works**
> 📖 Read the v0.5.0 article — [jump to Pipeline Architecture](https://medium.com/@alborznazari4/open-intelligence-lab-v0-5-0-from-research-platform-to-production-ci-cd-pipeline-4fb56cd21cd7)


> 📖 Read the full article: [From a Black Box to a Transparent, Modular, and Open-Source Model](https://medium.com/@alborznazari4/open-intelligence-lab-on-git-from-a-black-box-to-a-transparent-modular-and-open-source-model-ffa154962964)

**Visual Lab**
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

Run `demo.py` and an **interactive browser dashboard** opens showing the full threat knowledge graph — click any node to inspect its risk score, confidence, connections, and intelligence rationale.


## Repository Architecture
```
open-intelligence-lab/
├── demo.py                        ← Entry point — runs the full pipeline
├── index.html                     ← Visual Lab (GitHub Pages)
├── Dockerfile                     ← ★ v0.4.0 — Container build for OI Lab API
├── docker-compose.yml             ← ★ v0.4.0 — Full stack: OI Lab + MISP instance
├── .gitlab-ci.yml                 ← ★ v0.5.0 — 5-stage GitLab CI/CD pipeline
├── wrangler.jsonc                 ← ★ v0.5.0 — Cloudflare Workers scoped to visualization/
│
├── scripts/                       ← ★ v0.5.0 — CI helper scripts
│   ├── validate_schemas.py        ← Dataset JSON and STIX export validation
│   └── smoke_test.py              ← API endpoint smoke test (called by CI)
│
├── tests/                         ← ★ v0.5.0 — pytest suite
│   ├── __init__.py                ← Package marker
│   └── test_placeholder.py        ← Placeholder suite — full coverage in v0.5.1
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
│   ├── main.py                    ← FastAPI app entry point + MISP lifespan wiring
│   └── intelligence/
│       ├── router.py              ← GET /intelligence/analyze/{entity_id}
│       ├── service.py             ← Pipeline orchestration
│       └── schemas.py            ← Pydantic response models
│
├── backend/
│   ├── stix_exporter.py           ← ★ v0.3.0 — STIX 2.1 bundle builder + platform exporters
│   ├── taxii_server.py            ← ★ v0.3.0 / v0.4.0 — TAXII 2.1 server (publish + ingest endpoints)
│   ├── misp_client.py             ← ★ v0.4.0 — MISP REST API client + STIX normalization
│   ├── taxii_ingestor.py          ← ★ v0.4.0 — TAXII 2.1 feed subscriber (external feeds)
│   ├── feed_scheduler.py          ← ★ v0.4.0 — Ingestion orchestrator + live object store
│   ├── provenance.py              ← ★ v0.4.0 — Chain-of-custody engine + trust scoring
│   └── requirements.txt          ← Backend/server reference dependencies
│
└── exports/                       ← ★ v0.3.0 — Generated STIX export files (git-ignored)
    ├── stix_bundle.json           ← Raw STIX 2.1 bundle (OpenCTI)
    ├── splunk_events.json         ← Splunk ES sourcetype=stix events
    ├── sentinel_indicators.json   ← Microsoft Sentinel TI blade format
    ├── opencti_bundle.json        ← OpenCTI STIX 2.1 import bundle
    ├── qradar_objects.json        ← IBM QRadar flat STIX object list
    └── export_summary.json        ← Run metadata (timestamp, bundle ID, object count)
```


<img width="928" height="916" alt="Medium_02" src="https://github.com/user-attachments/assets/769d41e7-2bca-4b4b-978b-01c58a1e095b" />


## Quick Start

Two ways to run the project. Choose based on what you need.

---

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
> 

#### 4 — Run the Visual Lab

Open `index.html` directly in your browser for the full interactive graph.

#### 5 — Run the API

```bash
python -m uvicorn api.main:app --reload --port 8000
```

- **Interactive docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health check:** [http://localhost:8000/](http://localhost:8000/)

#### 6 — Run the Demo Pipeline

```bash
python demo.py
```

Your browser opens automatically with the interactive threat knowledge graph. In the terminal you'll see the full risk analysis report printed for all entities.

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


## v0.3.0 — STIX 2.1 Interoperability

v0.3.0 adds full **STIX 2.1** compliance across the dataset layer and a **TAXII 2.1** server that threat intelligence platforms can poll as a live feed. The platform is now natively interoperable with four industry-standard tools — no custom connectors required on their end.

### What STIX 2.1 Means Here

STIX (Structured Threat Information eXpression) is the OASIS standard for exchanging threat intelligence as typed, linked JSON objects. Every internal entity type maps to a corresponding STIX object:

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

Custom fields use the `x_oi_` prefix convention — transparent and separable from core STIX properties.

### Platform Integration

| Platform | Method | Format | Status |
|---|---|---|---|
| **Splunk Enterprise Security** | STIX-TAXII connector | `sourcetype=stix` events → `threat_intelligence` index | ✅ Ready |
| **Microsoft Sentinel** | Threat Intelligence blade (TAXII) | STIX 2.1 indicator objects → `ThreatIntelligenceIndicator` table | ✅ Ready |
| **OpenCTI** | Native STIX 2.1 import or TAXII poll | Raw STIX 2.1 bundle | ✅ Ready |
| **IBM QRadar SIEM** | STIX connector app | Flat STIX object list mapped to offense magnitude | ✅ Ready |

### Running the STIX Export

```bash
python backend/stix_exporter.py
```

This writes the following to `exports/`:

```
exports/
├── stix_bundle.json           ← Raw STIX 2.1 — use for OpenCTI or any STIX-native tool
├── splunk_events.json         ← Splunk ES sourcetype=stix events
├── sentinel_indicators.json   ← Sentinel Threat Intelligence blade format
├── opencti_bundle.json        ← OpenCTI STIX 2.1 import (same as raw bundle)
├── qradar_objects.json        ← IBM QRadar flat object list
└── export_summary.json        ← Timestamp, bundle ID, total object count
```

### Running the TAXII 2.1 Server

```bash
python -m uvicorn backend.taxii_server:app --host 0.0.0.0 --port 8000
```

TAXII endpoints:

| Endpoint | Description |
|---|---|
| `GET /taxii/` | Discovery — required by all TAXII 2.1 clients |
| `GET /taxii/api-root/` | API root metadata |
| `GET /taxii/api-root/collections/` | Lists all available collections |
| `GET /taxii/api-root/collections/{id}/objects/` | Returns STIX objects (paginated) |
| `GET /taxii/api-root/collections/{id}/manifest/` | Lightweight ID/version listing |
| `GET /taxii/health` | Health check — returns object count and server time |
| `GET /taxii/docs` | Interactive API documentation |

**Query parameters supported on the objects endpoint:**

| Parameter | Description | Example |
|---|---|---|
| `?limit=` | Max objects to return (1–1000, default 100) | `?limit=50` |
| `?added_after=` | Temporal filter (ISO 8601) | `?added_after=2024-01-01T00:00:00Z` |
| `?match[type]=` | Filter by STIX object type | `?match[type]=threat-actor` |

TAXII collections:

| Collection ID | Contents |
|---|---|
| `oi-lab-threat-actors-001` | Threat actor and identity objects |
| `oi-lab-attack-patterns-002` | MITRE-mapped attack patterns |
| `oi-lab-campaigns-003` | Diamond Model campaign objects |
| `oi-lab-full-bundle-004` | Complete STIX 2.1 bundle — all types |

### Connecting Splunk Enterprise Security

1. In Splunk ES, navigate to **Configure → Threat Intelligence → Intelligence Downloads**
2. Add a new TAXII source pointing to `http://your-host:8000/taxii/`
3. Select collection `oi-lab-full-bundle-004` for the complete dataset
4. Set polling interval — recommended 1 hour for a research feed
5. Risk scores appear as `x_oi_risk_score` fields, queryable via `tstats` and correlation rules

### Connecting Microsoft Sentinel

1. In Sentinel, open **Threat Intelligence → TAXII (Preview)**
2. Add connector: friendly name `OI Lab`, API root `http://your-host:8000/taxii/api-root/`
3. Collection: `oi-lab-full-bundle-004`
4. Indicators write into the `ThreatIntelligenceIndicator` table automatically
5. Build KQL hunting queries against `ThreatIntelligenceIndicator | where ConfidenceScore > 90`

### Connecting OpenCTI

**Option A — File import (fastest):**
1. Navigate to **Data → Import**
2. Select the **STIX 2.1** import connector
3. Upload `exports/opencti_bundle.json`
4. The knowledge graph appears inside OpenCTI with all relationships rendered as edges

**Option B — TAXII live feed:**
1. In OpenCTI, go to **Data → Ingestion → TAXII Feeds**
2. Add feed: URL `http://your-host:8000/taxii/api-root/`, collection `oi-lab-full-bundle-004`
3. Set polling interval and enable the feed

### Connecting IBM QRadar

1. Install the **STIX Threat Intelligence** app from IBM App Exchange (>= v3.x)
2. In QRadar, navigate to **Admin → STIX-TAXII Feed Management**
3. Add feed: TAXII server `http://your-host:8000/taxii/api-root/`, collection `oi-lab-full-bundle-004`
4. Map `oi_risk_score` to QRadar's offense magnitude field in the connector settings
5. Alternatively, use `exports/qradar_objects.json` for a one-time flat import


## v0.4.0 — Live Feed Ingestion + Provenance Validation

v0.4.0 makes the platform **bidirectional**. Where v0.3.0 made OI Lab a publisher — exporting STIX bundles and serving a TAXII feed — v0.4.0 adds the subscriber side: pulling live intelligence from external MISP instances and TAXII feeds, validating it through a provenance engine, and merging it into the knowledge graph.

### New Backend Modules

| File | Role |
|---|---|
| `backend/misp_client.py` | Connects to any MISP instance via its REST API. Pulls events and attributes, normalizes each to the correct STIX 2.1 type, and passes them to the provenance engine. |
| `backend/taxii_ingestor.py` | TAXII 2.1 client — performs discovery, enumerates collections, and fetches paginated STIX objects from any external TAXII server with `added_after` temporal filtering. |
| `backend/provenance.py` | Chain-of-custody engine. Every ingested object receives a `ProvenanceRecord` carrying `source`, `reported_by`, `original_timestamp`, `ingested_at`, `trust_level`, `staleness_days`, and a rejection reason if validation fails. |
| `backend/feed_scheduler.py` | Orchestrates ingestion cycles across all configured feeds. Maintains a live in-memory object store keyed by STIX ID. Runs as a background thread (hourly by default) or triggered manually via the API. |

### Activating the Live Feed

Set two environment variables before starting the API server:

```bash
# Linux / macOS
export MISP_URL=https://your-misp-instance.org
export MISP_KEY=your-api-key
python -m uvicorn api.main:app --reload --port 8000
```

```powershell
# Windows PowerShell
$env:MISP_URL = "https://your-misp-instance.org"
$env:MISP_KEY  = "your-api-key"
python -m uvicorn api.main:app --reload --port 8000
```

Without these variables the server starts normally on static datasets. With them, the scheduler activates automatically and the graph begins updating every hour.

**Additional optional variables:**

| Variable | Default | Description |
|---|---|---|
| `MISP_LABEL` | `MISP-Live` | Human-readable feed label in audit logs |
| `MISP_PULL_DAYS` | `7` | How many days back to fetch on each run |
| `MISP_LIMIT` | `200` | Max events per ingestion cycle |
| `MISP_VERIFY_SSL` | `true` | Set to `false` for self-signed certs (local Docker MISP) |
| `MISP_INTERVAL_SECONDS` | `3600` | Ingestion interval in seconds |

### Provenance Validation

Every object ingested from a MISP or TAXII feed passes through the provenance engine before entering the graph:

```
Source trust prior  ×  feed-level confidence  —  staleness penalty  =  adjusted trust level
```

| Signal | Effect |
|---|---|
| Source (e.g. MISP-CISA) | Applies a named trust prior (CISA = 1.0, unknown TAXII = 0.60) |
| MISP threat level | Converts threat level 1–4 to a confidence band (0.95 → 0.25) |
| Object age | Objects older than 90 days receive a −0.20 staleness penalty |
| Trust floor | Objects below 0.10 after all adjustments are rejected entirely |

Objects that pass validation are stamped with `x_oi_` chain-of-custody fields: `x_oi_source`, `x_oi_reported_by`, `x_oi_trust_level`, `x_oi_ingested_at`, `x_oi_staleness_days`, `x_oi_is_stale`.

### New TAXII Server Endpoints (v0.4.0)

Seven new endpoints added to `backend/taxii_server.py`:

| Endpoint | Description |
|---|---|
| `POST /ingest/misp` | Register a MISP instance and run an immediate ingestion cycle |
| `POST /ingest/taxii` | Register an external TAXII feed and ingest all readable collections |
| `POST /ingest/run` | Manually trigger one ingestion cycle across all configured feeds |
| `GET /ingest/objects` | Query the live ingested object store with type, source, and trust filters |
| `GET /ingest/store/summary` | Live store stats: object count, by type, by source, average trust level |
| `GET /ingest/run-log` | Per-feed audit log of every ingestion cycle |
| `GET /ingest/bundle` | Export all ingested objects as a STIX 2.1 bundle |

### Docker — Running the Full Stack

v0.4.0 ships a `Dockerfile` and `docker-compose.yml` that spin up the OI Lab API and a full local MISP instance together.

```bash
docker compose up
```

Services started:

| Service | URL | Credentials |
|---|---|---|
| OI Lab API | `http://localhost:8000` | — |
| OI Lab Docs | `http://localhost:8000/docs` | — |
| MISP UI | `https://localhost` | `admin@admin.test` / `admin` |

After MISP initializes (~2 minutes), get your API key from **My Profile → Auth key** in the MISP UI, then:

```bash
MISP_KEY=your-key docker compose up
```

Or add it to a `.env` file:
```
MISP_KEY=your-key
```

> **SSL note:** The local Docker MISP uses a self-signed certificate. `docker-compose.yml` sets `MISP_VERIFY_SSL=false` for container-to-container communication automatically. Do not disable SSL verification when connecting to a production MISP instance.

### The Feedback Loop

```
MISP (CERTs / ISACs)  ──┐
External TAXII feeds  ──┤──► Provenance engine ──► Live object store ──► STIX export
OpenCTI               ──┘                                                     ↓
                                                                   Splunk / Sentinel / QRadar
```

The platform now consumes community intelligence, validates its chain of custody, enriches the knowledge graph, and re-exports the unified result — closing the loop that v0.3.0 left open.

## v0.5.0 — GitLab CI/CD Pipeline + Production Infrastructure

v0.5.0 operationalizes the platform. Every commit to main now goes through eight automated checks before a human decides to deploy.

### Pipeline — 5 Stages, 10 Jobs

| Stage | Jobs | Purpose |
|-------|------|---------|
| validate | `lint`, `schema_validate` | flake8/black/isort code quality. STIX bundle and dataset JSON validation on every commit. |
| test | `unit_tests`, `api_smoke_test` | pytest with coverage. Live FastAPI server spun up in CI — real endpoints, real datasets, not mocks. |
| build | `build_docker`, `tag_release` | Docker image built with commit SHA tag, pushed to GitLab Container Registry. |
| security | `dependency_scan`, `container_scan` | pip-audit + safety on requirements.txt. Trivy scans Docker image for HIGH/CRITICAL CVEs. |
| deploy | `deploy_production`, `rollback_production` | Manual-gate deploy to Fly.io. One-click rollback via `ROLLBACK_SHA` variable. |

### New Files

| File | Description |
|------|-------------|
| `.gitlab-ci.yml` | 5-stage GitLab CI/CD pipeline |
| `scripts/validate_schemas.py` | Dataset and STIX export validation called by CI |
| `scripts/smoke_test.py` | API smoke test called by CI |
| `tests/test_placeholder.py` | Placeholder pytest suite — full coverage in v0.5.1 |
| `wrangler.jsonc` | Cloudflare Workers scoped to `visualization/` only |

### GitLab Pipeline
```
https://gitlab.com/alborznazari4/open-intelligence-lab/-/pipelines
```

## Core Principles

- **Public data only** — no private, scraped, or sensitive information
- **Explainability first** — every risk score must be traceable and expressible in plain language
- **Modular architecture** — each layer can be replaced or extended independently
- **Research transparency** — datasets, scoring logic, and relationships are fully visible
- **Ethical OSINT** — aligned with academic norms and MITRE ATT&CK attribution standards
- **Standard-first interoperability** — STIX 2.1 / TAXII 2.1 compliance ensures plug-and-play integration with the industry's leading platforms


## Roadmap

| Version | Focus | Status |
|---|---|---|
| **v0.1.0** | Core graph engine, datasets, API, Visual Lab | ✅ Complete |
| **v0.2.0** | FastAPI backend live; full-stack connected | ✅ Complete |
| **v0.3.0** | STIX 2.1 export, TAXII 2.1 server, Splunk / Sentinel / OpenCTI / QRadar interop | ✅ Complete |
| **v0.4.0** | MISP integration, TAXII feed ingestion, provenance validation, Docker support | ✅ Complete |
| **v0.5.0** | GitLab CI/CD pipeline, Docker build, security scanning, production deploy gate | ✅ Complete |
| **v1.0.0** | Neo4j backend, multi-hop actor pivoting, ML scoring with SHAP explainability | 🗓 Planned |


## Contributing

Contributions are welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md) and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before submitting a pull request.


## License

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/AlborzNazari/open-intelligence-lab/blob/main/LICENSE)

## How to Use MISP Data in the Visual Lab

Once MISP is connected and the live feed is active, the knowledge graph updates automatically every hour. Here is what happens and how to read it.

### What MISP Sends

Every hour the scheduler pulls recent events from your MISP instance. Each event contains attributes — structured threat observations: IP addresses, file hashes, domains, malware names, threat actor profiles. Each attribute is converted to a STIX 2.1 object and enters the graph as a new node, connected to existing entities where attribution is confident enough.

### Reading Live Nodes in the Graph

Click any node in the Visual Lab. The detail panel shows:

- **Source** — which MISP instance reported it (`MISP-Local`, `MISP-CIRCL`, etc.)
- **Trust level** — score from 0.0 to 1.0 based on MISP threat level and source trust prior
- **Ingested at** — when OI Lab pulled it from the feed
- **Staleness** — flagged if the intelligence is older than 90 days

### Querying Ingested Data via the API

| Endpoint | What it returns |
|---|---|
| `GET /ingest/objects?source=MISP-Local` | All objects ingested from your local MISP |
| `GET /ingest/objects?min_trust=0.8` | Only high-confidence objects |
| `GET /ingest/run-log` | History of every ingestion cycle |
| `GET /ingest/store/summary` | Object count by type and source |
| `GET /ingest/bundle` | Full STIX 2.1 export of all ingested objects |

### What the MISP Status Panel Means

| Status | Meaning |
|---|---|
| **Live Feed — Active** | `MISP_URL` and `MISP_KEY` are set, scheduler running |
| **Live Feed — Requires MISP Instance** | Env vars not set — static data only |
| **Provenance — Chain-of-Custody Active** | Every ingested object is stamped and validated |

### Trust Prior Reference

| Source | Trust Prior |
|---|---|
| MISP-CISA | 1.00 |
| MISP-CERT-EU / MISP-CIRCL / MISP-NATO | 0.95 |
| MISP-Community | 0.75 |
| TAXII-OpenCTI | 0.85 |
| TAXII-Unknown | 0.60 |

Objects older than 90 days receive a −0.20 staleness penalty. Objects below 0.10 trust after all adjustments are rejected entirely.

### Adding More Feeds

Register a second MISP instance or any TAXII 2.1 feed via the API:

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


## Troubleshooting

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for the full guide covering:

- Windows two-Python problem and module not found errors
- Mixed content block (GitHub Pages HTTPS vs local HTTP API)
- Docker network issues and port conflicts
- MISP initialization and API key setup
- Caddy 502 errors



*Open Intelligence Lab · Alborz Nazari · 2026 · [medium.com/@alborznazari4](https://medium.com/@alborznazari4)*
