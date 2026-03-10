# Changelog

All notable changes to Open Intelligence Lab are documented here.

---

## [v0.1.0] — 2026-03-10 — First Public Release

### Added
- Full threat knowledge graph pipeline: `graph_builder.py` → `risk_analyzer.py` → `intelligence_explainer.py`
- 5 JSON datasets: 21 entities, 15 attack patterns, 28 relations, 7 campaigns, MITRE ATT&CK mappings
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

### Known Limitations
- Dataset is static (v1 intentional design decision — see Medium article)
- In-memory NetworkX graph (not suitable for production scale > ~500 nodes)
- No authentication on the API layer
- STIX 2.1 compliance planned for v0.2

---

## Roadmap

- **v0.2** — STIX 2.1 schema, TAXII feed validation, OpenCTI integration
- **v0.3** — Neo4j backend, multi-hop Cypher queries, live IOC ingestion
- **v1.0** — ML risk scoring, SHAP explainability, full web UI
