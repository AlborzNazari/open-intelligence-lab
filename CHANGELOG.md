# Changelog

All notable changes to Open Intelligence Lab are documented here.

---
## [v0.5.0] — Planned — Test Suite, CI/CD Pipeline, Cloud Deployment

### Summary
v0.5.0 establishes the maintenance and reliability foundation. CI without tests is automating nothing — so this version ships a real pytest suite covering the graph engine, risk scorer, API endpoints, and provenance engine first, then wires it into a GitHub Actions CI pipeline that runs on every push and pull request. The CD side deploys the API to Fly.io, giving the platform a permanent public HTTPS endpoint and eliminating the localhost dependency for the Visual Lab entirely.

### Added

**Test Suite (`tests/`)**
- `tests/test_graph_builder.py` — graph structure, node count (37), edge count (28), presence of all known entity IDs, node attributes, edge wiring for known relations (APT28→X-Agent, Cl0p→CVE-2023-34362, LockBit→Healthcare)
- `tests/test_risk_analyzer.py` — score bounds [0.0, 1.0], score clamping, degree-weighted scoring, threat actor baseline floor, compute_all_risks return type
- `tests/test_api.py` — all REST endpoints: root health check, graph summary counts, edges, entity list with search/filter/pagination, analyze for all 17 known entity IDs, 404 for unknown IDs, risk score bounds validation
- `tests/test_provenance.py` — record creation, trust prior application, staleness detection at 90-day threshold, trust penalty for stale objects, rejection below minimum trust floor, dict serialization
- `tests/__init__.py` — package marker
- `pyproject.toml` — pytest configuration (testpaths, addopts, verbosity)

**CI Pipeline (`.github/workflows/ci.yml`)**
- Runs on every push to `main` and every pull request
- Matrix: Python 3.10, 3.11, 3.12 — tests must pass on all three
- Steps: checkout, setup-python with pip cache, install requirements + pytest + httpx + pytest-cov, run full test suite with coverage report
- Coverage artifact uploaded for Python 3.12 run
- Ruff linting job runs in parallel

**CD Pipeline (`.github/workflows/cd.yml`)**
- Deploys to Fly.io on every push to `main`
- Uses `superfly/flyctl-actions` — no manual deploy steps
- `FLY_API_TOKEN` stored as GitHub secret
- Gated behind CI passing (add `needs: [test]` once test suite is stable)

**Fly.io Deployment (`fly.toml`)**
- App region: `ams` (Amsterdam) — change to nearest region
- Force HTTPS: true — Fly.io handles TLS, Caddy not needed in production
- Auto-stop/start machines on traffic — zero cost when idle
- 512MB memory, shared CPU — sufficient for the NetworkX graph at current scale
- MISP env vars settable via `flyctl secrets set MISP_URL=... MISP_KEY=...`
- Public endpoint: `https://open-intelligence-lab.fly.dev`

### Changed
- `index.html` — when deployed, update `API_BASE` default to the Fly.io URL so GitHub Pages connects without any localhost dependency
- Roadmap updated: v0.5.0 marked planned, CI/CD and deployment added as explicit milestone

### Why This Matters
CI/CD without tests is noise. Tests without deployment are untested in production. v0.5.0 does both properly: the test suite verifies the platform actually works before any code ships, and the deployment pipeline puts the API on a real HTTPS URL that GitHub Pages can call without mixed content restrictions, without Docker, and without any local server running on the user's machine.

---



## [v0.4.0] — 2026-03-28 — Live Feed Ingestion, MISP Integration, Docker Stack

### Summary
v0.4.0 makes the platform **bidirectional**. Where v0.3.0 made OI Lab a publisher — exporting STIX bundles and serving a TAXII feed — v0.4.0 adds the subscriber side: pulling live intelligence from external MISP instances and TAXII feeds, validating it through a provenance engine, and merging it into the knowledge graph automatically. A full Docker stack eliminates the browser mixed-content block and reduces setup to a single command.

### Added

**MISP REST API Client (`backend/misp_client.py`)**
- Connects to any MISP instance (>= 2.4.x) via REST API over HTTPS
- Pulls recent events via `POST /events/restSearch` with configurable day range and limit
- Converts MISP attributes to correct STIX 2.1 object types: IP/domain/hash/URL → `indicator`, threat-actor → `threat-actor`, malware-type → `malware`, vulnerability → `vulnerability`, campaign-name → `campaign`
- Builds STIX patterning expressions for all IOC types (IPv4, domain, URL, MD5, SHA1, SHA256, filename)
- MISP threat level → confidence band mapping: High (1) = 0.95, Medium (2) = 0.75, Low (3) = 0.50, Undefined (4) = 0.25
- Distribution modifier: org-only events (−0.15), community/all (+0.05)
- Chain-of-custody extension fields (`x_oi_source`, `x_oi_misp_event_id`, `x_oi_ingested_at`, etc.) on every output object
- `test_connection()` method for verifying MISP connectivity before ingestion

**TAXII 2.1 Feed Ingestor (`backend/taxii_ingestor.py`)**
- TAXII 2.1 client — performs server discovery, collection enumeration, paginated object retrieval
- Supports `added_after` temporal filtering to avoid re-ingesting old objects
- Three authentication modes: API key (Authorization header), HTTP Basic, Bearer token
- `ingest_collection()` and `ingest_all_collections()` methods
- All ingested objects pass through the provenance engine before entering the object store

**Provenance Engine (`backend/provenance.py`)**
- Every ingested STIX object receives a `ProvenanceRecord` with: `source`, `reported_by`, `original_timestamp`, `ingested_at`, `trust_level`, `staleness_days`, `is_stale`, `feed_type`, `passed_validation`, `rejection_reason`
- Source trust priors: MISP-CISA = 1.00, MISP-CERT-EU / MISP-CIRCL / MISP-NATO = 0.95, MISP-Community = 0.75, TAXII-OpenCTI = 0.85, TAXII-Commercial = 0.80, TAXII-Unknown = 0.60
- Staleness threshold: 90 days — objects older than this receive −0.20 trust penalty and are flagged `is_stale=True`
- Minimum trust floor: 0.10 — objects below this after all adjustments are rejected entirely
- `ProvenanceEngine.validate()` applies full chain: source prior × feed confidence − staleness penalty
- All provenance records are keyed by STIX ID for audit retrieval

**Feed Scheduler (`backend/feed_scheduler.py`)**
- Orchestrates ingestion cycles across all configured MISP and TAXII feed sources
- Maintains a live in-memory object store keyed by STIX ID with last-write-wins deduplication
- `start_background(interval_seconds)` — runs ingestion as a daemon thread (default: 3600s)
- `run_once()` — manual single-cycle trigger, returns full run summary
- `get_ingested_objects()` — query store by STIX type, source label, minimum trust, staleness exclusion
- `export_as_stix_bundle()` — unified STIX 2.1 export of all validated ingested objects
- Per-run `FeedRunRecord` with: objects fetched, validated, rejected, stale count, error message, timestamps

**New TAXII Server Endpoints (`backend/taxii_server.py`)**
- `POST /ingest/misp` — register a MISP instance and run immediate ingestion cycle
- `POST /ingest/taxii` — register an external TAXII feed and ingest all readable collections
- `POST /ingest/run` — manually trigger one ingestion cycle across all configured feeds
- `GET /ingest/objects` — query live object store with `?type=`, `?source=`, `?min_trust=`, `?exclude_stale=`
- `GET /ingest/store/summary` — live stats: total objects, by type, by source, average trust level
- `GET /ingest/run-log` — per-feed audit log of every ingestion cycle (last 50 by default)
- `GET /ingest/bundle` — export all ingested objects as a STIX 2.1 bundle

**Updated API Entry Point (`api/main.py`)**
- Added FastAPI `lifespan` context manager for startup/shutdown hooks
- On startup: reads `MISP_URL` and `MISP_KEY` environment variables; if set, registers MISP feed and starts background scheduler automatically
- On shutdown: gracefully stops background scheduler
- Root endpoint now returns `misp_live_feed` status field indicating active/inactive state
- Supports `MISP_LABEL`, `MISP_PULL_DAYS`, `MISP_LIMIT`, `MISP_VERIFY_SSL`, `MISP_INTERVAL_SECONDS` env vars

**Docker Stack**
- `Dockerfile` — multi-stage Python 3.12-slim container for the OI Lab API
- `docker-compose.yml` — five-service stack: MariaDB, Redis, MISP core, OI Lab API, Caddy HTTPS proxy
- `Caddyfile` — Caddy reverse proxy config serving OI Lab API at `https://localhost:8443` with auto-generated self-signed cert
- Eliminates browser mixed-content block: GitHub Pages (HTTPS) → Caddy (HTTPS) → OI Lab API (HTTP internal)
- `index.html` updated: auto-detects page protocol and switches API base URL accordingly (`http://localhost:8000` for local file, `https://localhost:8443` for GitHub Pages)
- `.env` file support: set `MISP_KEY=your-key` in project root to activate live feed on `docker compose up`

**Documentation**
- `MISP_USAGE.md` — new standalone guide: what MISP data looks like in the graph, API query reference, trust prior table, adding multiple feeds
- `TROUBLESHOOTING.md` — fully rewritten with all real issues: two-Python problem, mixed content block fixes (Firefox, Chrome, Docker), Docker network errors, port conflicts, MISP init timing, Caddy 502
- `OIL_UserGuide.pdf` — full user guide PDF covering installation, Visual Lab, API, MISP, STIX export, and troubleshooting
- `README.md` — updated entity count (22), corrected campaign list, corrected risk formula, added Docker option, MISP usage section, troubleshooting pointer

### Changed
- `api/main.py` — replaced bare `app = FastAPI()` with lifespan-aware version; MISP scheduler wired at startup
- `index.html` — API base URL now auto-selects between HTTP (local file) and HTTPS (GitHub Pages) based on `location.protocol`
- `README.md` — entity count corrected from 21 to 22, campaign list corrected, risk formula corrected from `Likelihood × Impact × Confidence` to `base + degree_factor + incident_factor`
- Roadmap updated: v0.4.0 marked complete, v1.0.0 (Neo4j, ML scoring, SHAP) added

### Fixed
- Mixed content block when opening Visual Lab from GitHub Pages — resolved via Caddy HTTPS proxy and auto-switching API base URL
- Docker containers not joining the same network on Windows Docker Desktop — resolved by explicitly declaring `networks: oilab-net` on every service
- `ModuleNotFoundError: No module named 'networkx'` on Windows with multiple Python installations — documented fix in TROUBLESHOOTING.md

### Technical Notes
- MISP tested against >= 2.4.x (official Docker image: `ghcr.io/misp/misp-docker/misp-core:latest`)
- Docker stack requires Docker Desktop 25+ or Docker Engine 25+
- Caddy uses `tls internal` — self-signed cert, accept browser warning once
- MISP Docker requires companion MariaDB and Redis — both included in `docker-compose.yml`
- Background scheduler is a daemon thread — stops automatically when the FastAPI process exits

---

## [v0.3.0] — 2026-03-12

### Added

**STIX 2.1 Export Engine (`backend/stix_exporter.py`)**
- Full STIX 2.1 bundle builder from OI Lab datasets
- Entity type mapping: threat_actor → `threat-actor`, malware → `malware`, infrastructure → `infrastructure`, CVE → `vulnerability`, sector → `identity`
- Attack patterns map to STIX `attack-pattern` with kill chain phases and MITRE external references
- Relations from `relations.json` become STIX `relationship` objects with confidence preserved
- Campaigns from `campaigns.json` become STIX `campaign` objects with Diamond Model fields as `x_oi_` extensions
- Confidence conversion: internal [0.0, 1.0] float → STIX integer [0, 100]
- Custom extension prefix `x_oi_` for non-standard fields (risk_score, entity_id, diamond model attributes)

**Platform-Specific Exporters**
- `export_for_splunk()` — formats STIX bundle as Splunk sourcetype events (index: `threat_intelligence`)
- `export_for_sentinel()` — Sentinel Threat Intelligence blade format with `x-open-intelligence-lab` extension block
- `export_for_opencti()` — raw STIX 2.1 bundle (OpenCTI ingests natively)
- `export_for_qradar()` — flat row-oriented format for IBM QRadar STIX connector app

**TAXII 2.1 Server (`backend/taxii_server.py`)**
- FastAPI-based TAXII 2.1 server with full spec compliance
- Discovery endpoint: `GET /taxii/`
- API root: `GET /taxii/api-root/`
- Collections listing: `GET /taxii/api-root/collections/`
- Object retrieval with pagination (`?limit=`), temporal filter (`?added_after=`), type filter (`?match[type]=`)
- Manifest endpoint for lightweight ID/version listing
- Four collections: threat-actors, attack-patterns, campaigns, full-bundle
- Health check endpoint: `GET /taxii/health`
- CORS configured for cross-origin dashboard access

**Export Output Directory (`exports/`)**
- `stix_bundle.json` — raw STIX 2.1 bundle (OpenCTI)
- `splunk_events.json` — Splunk ES STIX events
- `sentinel_indicators.json` — Microsoft Sentinel indicator objects
- `opencti_bundle.json` — OpenCTI import bundle
- `qradar_objects.json` — IBM QRadar flat STIX objects
- `export_summary.json` — run metadata (timestamp, bundle ID, object count)

**Visual Lab Updates (`index.html`)**
- Added STIX 2.1 Export panel in right column with per-platform export preview buttons
- Added Platform Integration Status panel (Splunk, Sentinel, OpenCTI, QRadar, TAXII)
- v0.3.0 badge in header status bar
- STIX badge alongside MITRE ATT&CK badge

**README Updates**
- Full v0.3.0 interoperability section with platform connection instructions
- STIX 2.1 object mapping table
- Updated architecture flowchart with STIX layer
- TAXII collection reference table

### Changed
- Repository structure: added `backend/` as home for STIX/TAXII modules
- `exports/` directory added to `.gitignore` for generated files (bundle added separately for reference)
- Roadmap table updated: v0.3.0 marked complete, v0.4.0 (MISP + TAXII ingestion) added

### Technical Notes
- STIX 2.1 spec: https://docs.oasis-open.org/cti/stix/v2.1/os/stix-v2.1-os.html
- TAXII 2.1 spec: https://docs.oasis-open.org/cti/taxii/v2.1/os/taxii-v2.1-os.html
- Splunk ES STIX-TAXII connector: requires ES >= 7.x
- Sentinel TAXII connector: preview feature, Sentinel workspace required
- OpenCTI: tested against >= 5.x with STIX 2.1 import connector
- IBM QRadar: STIX Threat Intelligence app >= 3.x from IBM App Exchange
- TAXII server: `uvicorn backend.taxii_server:app --host 0.0.0.0 --port 8000`

---

## [v0.2.0] — 2026-03-10 — Full Stack Connected

### Summary
v0.2.0 completes the full-stack integration. The API, core engine, and dashboard now run as a single connected system. The knowledge graph loads from real datasets at startup, the API returns live risk scores, and the dashboard fetches everything from `localhost:8000` in real time.

### Added

**`core_engine/graph_builder.py`**
- `ThreatKnowledgeGraph.__init__()` now calls `_load_datasets()` automatically
- `_load_entities()` — loads all 22 entities from `datasets/threat_entities.json`
- `_load_attack_patterns()` — loads all 15 patterns from `datasets/attack_patterns.json`
- `_load_relations()` — loads all 28 relations from `datasets/relations.json` and wires them as directed edges between existing nodes
- Node attributes now use `label` and `type` keys (consistent with API layer)

**`api/intelligence/service.py`**
- `_get_graph()` — module-level singleton via `@lru_cache`; graph built once at startup, shared by all requests for the process lifetime
- `_get_analyzer()` — pre-computes all risk scores once at startup via `@lru_cache`
- `list_entities()` — search and filter all graph entities by `query` (substring), `min_risk`, `max_risk`, `entity_type`; results sorted highest-risk first; paginated
- `get_graph_summary()` — returns node count, edge count, avg/max/min risk scores
- `analyze_entity()` now raises `KeyError` for unknown entity IDs (surfaced as HTTP 404)

**`api/intelligence/router.py`**
- `GET /intelligence/entities` — search/filter endpoint with full query parameter support
- `GET /intelligence/graph/summary` — live graph statistics for dashboard health cards
- `GET /intelligence/entities/ids` — lightweight flat list of all entity IDs for autocomplete

**`api/main.py`**
- `CORSMiddleware` added — allows the dashboard (opened via `file://` or any `localhost` port) to call the API without browser CORS errors
- `"null"` included as allowed origin so `file://` HTML files work correctly
- API version set to `0.2.0` in FastAPI metadata

**`demo.py`**
- Dashboard now fetches live data from `localhost:8000` via vanilla JS `fetch()`
- Summary cards populated from `GET /intelligence/graph/summary`
- Entity table loaded from `GET /intelligence/entities` with 20 results per page
- Search box, min/max risk filters, and entity type filter all call the API in real time
- Pagination controls (Prev / Next) with page counter

**`requirements.txt`**
- Added `fastapi==0.115.0`
- Added `uvicorn[standard]==0.30.6`

### Changed
- `ThreatKnowledgeGraph` no longer requires manual entity/relation loading — datasets are loaded automatically in `__init__()`
- Graph node attribute keys unified: `label` (display name), `type` (entity type)

### Fixed
- API previously returned an empty graph because `service.py` called `kg.get_graph()` before any data was loaded
- `requirements.txt` was missing `fastapi` and `uvicorn`, breaking fresh installs

### Known Limitations
- Dataset is still static JSON
- In-memory NetworkX graph (not suitable for > ~500 nodes)
- No authentication on the API layer

---

## [v0.1.0] — 2026-02-28 — First Public Release

### Added
- Full threat knowledge graph pipeline: `graph_builder.py` → `risk_analyzer.py` → `intelligence_explainer.py`
- 5 JSON datasets: 22 entities, 15 attack patterns, 28 relations, 7 campaigns, MITRE ATT&CK mappings
- Interactive browser dashboard launched from `demo.py` — zoomable, pannable, clickable graph
- Risk scoring model: base risk + degree factor + incident weighting, bucketed into CRITICAL / HIGH / MEDIUM / LOW
- Plain-language explainability rationale for every entity risk score
- FastAPI REST API with `/intelligence/analyze/{entity_id}` endpoint
- Entity registry: APT28, APT29, APT41, Lazarus Group, LockBit, Cl0p, KillNet + malware, CVEs, infrastructure, sectors
- MITRE ATT&CK alignment for all threat actors and attack patterns
- Diamond Model encoding for all 7 campaigns
- MIT License, CODE_OF_CONDUCT.md, CONTRIBUTING.md

### Architecture
- `datasets/` → `core_engine/` → `api/` → `visualization/` pipeline
- Modular design — each layer independently replaceable
- Pure Python + browser Canvas visualization (no heavy frontend framework required)

### Known Limitations
- Dataset is static (intentional design decision for v1)
- In-memory NetworkX graph (not suitable for production scale > ~500 nodes)
- No authentication on the API layer
- Dashboard and API were not connected — dashboard read JSON files directly

---

## Roadmap

| Version | Focus | Status |
|---|---|---|
| **v0.1.0** | Core graph engine, datasets, API, Visual Lab | ✅ Complete |
| **v0.2.0** | FastAPI backend live, full-stack connected | ✅ Complete |
| **v0.3.0** | STIX 2.1 export, TAXII 2.1 server, platform interoperability | ✅ Complete |
| **v0.4.0** | MISP integration, TAXII ingestion, provenance validation, Docker stack | ✅ Complete |
| **v1.0.0** | Neo4j backend, multi-hop Cypher queries, ML scoring with SHAP explainability | 🗓 Planned |

---

*Open Intelligence Lab — MIT License*
*github.com/AlborzNazari/open-intelligence-lab*
