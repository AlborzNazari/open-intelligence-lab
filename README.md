# Open Intelligence Lab

[![Research Status](https://img.shields.io/badge/research-alpha-blue)](https://github.com/AlborzNazari/open-intelligence-lab)
[![Dataset Version](https://img.shields.io/badge/datasets-v0.1-green)](https://github.com/AlborzNazari/open-intelligence-lab/tree/main/datasets)
[![Model Version](https://img.shields.io/badge/intelligence_model-v0.3-orange)](https://github.com/AlborzNazari/open-intelligence-lab)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![MITRE ATT&CK](https://img.shields.io/badge/MITRE-ATT%26CK%20Aligned-red)](https://attack.mitre.org/)
[![STIX 2.1](https://img.shields.io/badge/STIX-2.1%20Compliant-8b5cf6)](https://oasis-open.github.io/cti-documentation/stix/intro)
[![TAXII 2.1](https://img.shields.io/badge/TAXII-2.1%20Server-7c3aed)](https://docs.oasis-open.org/cti/taxii/v2.1/os/taxii-v2.1-os.html)

**Open Intelligence Lab** is an ethical OSINT research platform focused on public-security intelligence representation, graph-based threat modeling, and explainable risk analytics.

It provides a clean, modular environment for researchers, analysts, and engineers who want to explore open-source intelligence signals **without compromising privacy or ethics** — using only public data, with every risk score backed by an interpretable rationale.

As of **v0.3.0**, the platform is fully interoperable with Splunk Enterprise Security, Microsoft Sentinel, OpenCTI, and IBM QRadar via STIX 2.1 exports and a built-in TAXII 2.1 server.

**How the Software Works**
> 📖 Read the full article: [From a Black Box to a Transparent, Modular, and Open-Source Model](https://medium.com/@alborznazari4/open-intelligence-lab-on-git-from-a-black-box-to-a-transparent-modular-and-open-source-model-ffa154962964)

**Visual Lab**
> 🔬 Explore the live graph: [alborznazari.github.io/open-intelligence-lab](https://alborznazari.github.io/open-intelligence-lab/)


## What Does This Software Do?

Open Intelligence Lab models real-world threat intelligence as a **traversable knowledge graph**:

- **21 entities** — threat actors (APT28, APT29, APT41, Lazarus, LockBit, Cl0p, KillNet), malware families, CVEs, infrastructure nodes, and target sectors
- **28 documented relations** — `uses`, `exploits`, `targets`, `uses_pattern`, `related_to`
- **7 real campaigns** — SolarWinds, MOVEit, LockBit 3.0, Bybit Heist, and more
- **Risk scoring** — every entity gets a score from 0.0 to 1.0 computed from threat likelihood × impact × confidence, bucketed into `LOW / MEDIUM / HIGH / CRITICAL`
- **Explainability** — every risk score produces a plain-language rationale, never a naked number
- **MITRE ATT&CK alignment** — all actors and patterns are mapped to official technique IDs
- **STIX 2.1 export** *(v0.3.0)* — full bundle export for Splunk, Sentinel, OpenCTI, and QRadar
- **TAXII 2.1 server** *(v0.3.0)* — live feed endpoint that threat platforms can poll directly

Run `demo.py` and an **interactive browser dashboard** opens showing the full threat knowledge graph — click any node to inspect its risk score, confidence, connections, and intelligence rationale.


## Repository Architecture

open-intelligence-lab/
├── demo.py                        ← Entry point — runs the full pipeline
├── index.html                     ← Visual Lab (GitHub Pages)
│
├── datasets/                      ← 5 JSON knowledge base files
│   ├── threat_entities.json       ← 21 entities (actors, malware, CVEs, sectors, infra)
│   ├── attack_patterns.json       ← 15 OSINT attack patterns with MITRE mappings
│   ├── relations.json             ← 28 directed edges (the graph lives here)
│   ├── campaigns.json             ← 7 real-world campaigns (Diamond Model)
│   └── mitre_mapping.json         ← ATT&CK technique profiles per actor
│
├── core_engine/                   ← Intelligence pipeline
│   ├── graph_builder.py           ← Builds DiGraph from datasets (NetworkX)
│   ├── risk_analyzer.py           ← Risk = Likelihood × Impact × Confidence
│   ├── intelligence_explainer.py  ← Plain-language rationale generator
│   └── intelligence_entities.py  ← Entity data model
│
├── visualization/
│   └── graph_renderer.py          ← Interactive browser graph (Canvas + D3-style)
│
├── api/
│   ├── main.py                    ← FastAPI app entry point
│   └── intelligence/
│       ├── router.py              ← GET /intelligence/risk/{entity_id}
│       ├── service.py             ← Pipeline orchestration
│       └── schemas.py            ← Pydantic response models
│
├── backend/
│   ├── stix_exporter.py           ← ★ v0.3.0 — STIX 2.1 bundle builder + platform exporters
│   ├── taxii_server.py            ← ★ v0.3.0 — TAXII 2.1 FastAPI server
│   └── requirements.txt          ← API/server dependencies
│
└── exports/                       ← ★ v0.3.0 — Generated STIX export files (git-ignored)
    ├── stix_bundle.json           ← Raw STIX 2.1 bundle (OpenCTI)
    ├── splunk_events.json         ← Splunk ES sourcetype=stix events
    ├── sentinel_indicators.json   ← Microsoft Sentinel TI blade format
    ├── opencti_bundle.json        ← OpenCTI STIX 2.1 import bundle
    ├── qradar_objects.json        ← IBM QRadar flat STIX object list
    └── export_summary.json        ← Run metadata (timestamp, bundle ID, object count)
```

---

<img width="928" height="916" alt="Medium_02" src="https://github.com/user-attachments/assets/769d41e7-2bca-4b4b-978b-01c58a1e095b" />


## Quick Start

### Prerequisites

- **Python 3.10+** — [python.org/downloads](https://www.python.org/downloads/)
- **Git** — [git-scm.com](https://git-scm.com/)

Verify:
```bash
python --version   # must be 3.10+
git --version
```

### 1 — Clone

```bash
git clone https://github.com/AlborzNazari/open-intelligence-lab.git
cd open-intelligence-lab
```

### 2 — Create Virtual Environment

```bash
python -m venv venv
```

Activate:

| Platform | Command |
|----------|---------|
| Windows (PowerShell) | `venv\Scripts\activate.bat` |
| macOS / Linux | `source venv/bin/activate` |

You should see `(venv)` at the start of your prompt.

> **Windows note:** If you get a script execution error, run this first:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

### 3 — Install Dependencies

```bash
pip install -r requirements.txt
pip install -r backend/requirements.txt
```

> **Windows note:** If any package fails to build from source, use:
> ```bash
> pip install -r requirements.txt --only-binary=:all:
> ```

### 4 — Run the Software

```bash
python demo.py
```

Your browser opens automatically with the **interactive threat knowledge graph**. In the terminal you'll see the full risk analysis report printed for all entities.


## Interactive Dashboard

When `demo.py` runs, it opens a browser dashboard with:

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


## Running the API

```bash
uvicorn api.main:app --reload --port 8000
```
If not working:
```bash
python -m uvicorn api.main:app --reload --port 8000
```
If still not working:
```bash
pip install uvicorn fastapi
```

Then repeat:
```bash
uvicorn api.main:app --reload --port 8000
```

- **Interactive docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Risk endpoint:** `http://localhost:8000/intelligence/risk/{entity_id}`

Example:
```bash
curl http://localhost:8000/intelligence/risk/TA-001
```


## Risk Model

```
Risk Score = (Threat Likelihood × Impact) × Confidence Weight
```

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
| `threat_entities.json` | 21 entities across 5 types | MITRE ATT&CK, CISA Advisories |
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
# Generate all platform-specific export files
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
uvicorn backend.taxii_server:app --host 0.0.0.0 --port 8000
```

If not working:
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
| **v0.2.0** | FastAPI backend live; `demo.py` → `service.py` wiring | ✅ Complete |
| **v0.3.0** | STIX 2.1 export, TAXII 2.1 server, Splunk / Sentinel / OpenCTI / QRadar interop | ✅ Complete |
| **v0.4.0** | MISP integration, TAXII feed ingestion with provenance validation | 🗓 Planned |
| **v1.0.0** | Neo4j backend, multi-hop actor pivoting, ML scoring with SHAP explainability | 🗓 Planned |


## Contributing

Contributions are welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md) and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before submitting a pull request.



## License

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/AlborzNazari/open-intelligence-lab/blob/main/LICENSE)




*Open Intelligence Lab · Alborz Nazari · 2026 · [medium.com/@alborznazari4](https://medium.com/@alborznazari4)*
