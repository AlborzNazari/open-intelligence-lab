# Changelog

All notable changes to Open Intelligence Lab are documented here.

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

## [v0.1.0] — 2026-02-28

### Added

- Core graph engine: `graph_builder.py`, `risk_analyzer.py`, `explainability.py`
- Dataset layer: 21 entities, 15 attack patterns, 28 relations, 7 campaigns
- FastAPI REST API: `api/intelligence/router.py`
- Visual Lab: `index.html` with force-directed graph, entity detail panel, campaign list
- Demo pipeline: `demo.py` end-to-end run writing to `research_docs/`
- MITRE ATT&CK alignment across attack patterns and actor profiles
- Diamond Model encoding in `campaigns.json`
- GitHub Pages deployment via `.github/workflows`
- README, CONTRIBUTING, CODE_OF_CONDUCT

---

*Open Intelligence Lab — MIT License*
*github.com/AlborzNazari/open-intelligence-lab*



## [v0.2.0] — 2026-03-10 — Full Stack Connected

### Summary
v0.2.0 completes the full-stack integration. The API, core engine, and dashboard
now run as a single connected system. The knowledge graph loads from real datasets
at startup, the API returns live risk scores, and the dashboard fetches everything
from `localhost:8000` in real time.

### Added

#### `core_engine/graph_builder.py`
- `ThreatKnowledgeGraph.__init__()` now calls `_load_datasets()` automatically
- `_load_entities()` — loads all 22 entities from `datasets/threat_entities.json`
- `_load_attack_patterns()` — loads all 15 patterns from `datasets/attack_patterns.json`
- `_load_relations()` — loads all 28 relations from `datasets/relations.json` and
  wires them as directed edges between existing nodes
- Node attributes now use `label` and `type` keys (consistent with API layer)

#### `api/intelligence/service.py`
- `_get_graph()` — module-level singleton via `@lru_cache`; graph built once at startup,
  shared by all requests for the process lifetime
- `_get_analyzer()` — pre-computes all risk scores once at startup via `@lru_cache`
- `list_entities()` — search and filter all graph entities by `query` (substring),
  `min_risk`, `max_risk`, `entity_type`; results sorted highest-risk first; paginated
- `get_graph_summary()` — returns node count, edge count, avg/max/min risk scores
- `analyze_entity()` now raises `KeyError` for unknown entity IDs (surfaced as HTTP 404)

#### `api/intelligence/router.py`
- `GET /intelligence/entities` — search/filter endpoint with full query parameter support
- `GET /intelligence/graph/summary` — live graph statistics for dashboard health cards
- `GET /intelligence/entities/ids` — lightweight flat list of all entity IDs for autocomplete

#### `api/main.py`
- `CORSMiddleware` added — allows the dashboard (opened via `file://` or any
  `localhost` port) to call the API without browser CORS errors
- `"null"` included as allowed origin so `file://` HTML files work correctly
- API version set to `0.2.0` in FastAPI metadata

#### `demo.py`
- Dashboard now fetches live data from `localhost:8000` via vanilla JS `fetch()`
- No JSON files are read directly anymore
- Summary cards populated from `GET /intelligence/graph/summary`
- Entity table loaded from `GET /intelligence/entities` with 20 results per page
- Search box, min/max risk filters, and entity type filter all call the API in real time
- "Analyze" button per row calls `GET /intelligence/analyze/{entity_id}` and shows
  live risk score + full explanation in a detail panel
- Red error banner shown if the API is not reachable (instead of silently showing stale data)
- Pagination controls (Prev / Next) with page counter

#### `requirements.txt`
- Added `fastapi==0.115.0`
- Added `uvicorn[standard]==0.30.6`
  (both were missing, causing `ModuleNotFoundError` on fresh install)

### Changed
- `ThreatKnowledgeGraph` no longer requires manual entity/relation loading — datasets
  are loaded automatically in `__init__()`
- Graph node attribute keys unified: `label` (display name), `type` (entity type)
  replacing inconsistent `name` / `entity_type` keys from v0.1.0

### Fixed
- API previously returned an empty graph because `service.py` called `kg.get_graph()`
  before any data was loaded — now fixed by dataset auto-loading in `graph_builder.py`
- `requirements.txt` was missing `fastapi` and `uvicorn`, breaking fresh installs

### Known Limitations
- Dataset is still static JSON (live feed ingestion planned for v0.3.0)
- In-memory NetworkX graph (not suitable for > ~500 nodes)
- No authentication on the API layer
- Attack pattern nodes referenced in `relations.json` via `OSINT-T*` IDs — relations
  to these nodes are wired correctly only if those IDs exist in `attack_patterns.json`

---

## [v0.1.0] — 2026-03-10 — First Public Release

### Added
- Full threat knowledge graph pipeline: `graph_builder.py` → `risk_analyzer.py` → `intelligence_explainer.py`
- 5 JSON datasets: 22 entities, 15 attack patterns, 28 relations, 7 campaigns, MITRE ATT&CK mappings
- Interactive browser dashboard launched from `demo.py` — zoomable, pannable, clickable graph
- Risk scoring model: Likelihood × Impact × Confidence, bucketed into CRITICAL / HIGH / MEDIUM / LOW
- Plain-language explainability rationale for every entity risk score
- FastAPI REST API with `/intelligence/risk/{entity_id}` endpoint
- Entity registry: APT28, APT29, APT41, Lazarus Group, LockBit, Cl0p, KillNet + malware, CVEs, infrastructure, sectors
- MITRE ATT&CK alignment for all threat actors and attack patterns
- Diamond Model encoding for all 7 campaigns
- MIT License, CODE_OF_CONDUCT.md, CONTRIBUTING.md

### Architecture
- `datasets/` → `core_engine/` → `api/` → `visualization/` pipeline
- Modular design — each layer independently replaceable
- Pure Python + browser Canvas visualization (no heavy frontend framework required)

### Known Limitations (at time of release)
- Dataset is static (v1 intentional design decision)
- In-memory NetworkX graph (not suitable for production scale > ~500 nodes)
- No authentication on the API layer
- Dashboard and API were not connected — dashboard read JSON files directly

---

## Roadmap

- **v0.3** — Neo4j backend, multi-hop Cypher queries, live IOC ingestion, STIX 2.1 schema
- **v1.0** — ML risk scoring, SHAP explainability, full React web UI, authentication
