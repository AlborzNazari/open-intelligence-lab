# Changelog

All notable changes to Open Intelligence Lab are documented here.

---

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
