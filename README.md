a# Open Intelligence Lab

[![Research Status](https://img.shields.io/badge/research-alpha-blue)](https://github.com/AlborzNazari/open-intelligence-lab)
[![Dataset Version](https://img.shields.io/badge/datasets-v0.1-green)](https://github.com/AlborzNazari/open-intelligence-lab)
[![Model Version](https://img.shields.io/badge/intelligence_model-v0.3-orange)](https://github.com/AlborzNazari/open-intelligence-lab)
[![STIX 2.1](https://img.shields.io/badge/STIX-2.1%20Compliant-8b5cf6)](https://oasis-open.github.io/cti-documentation/stix/intro)
[![TAXII 2.1](https://img.shields.io/badge/TAXII-2.1%20Server-7c3aed)](https://oasis-open.github.io/cti-documentation/taxii/intro)

Open Intelligence Lab is an ethical OSINT research platform focused on public‑security intelligence representation, graph‑based threat modeling, and explainable risk analytics. It provides a clean, modular environment for researchers, analysts, and engineers who want to explore open‑source intelligence signals **without compromising privacy or ethics**.

---

## 🧠 Vision & Philosophy

Security intelligence is often opaque, proprietary, and difficult to interpret. This project aims to change that by offering:

- **Transparent intelligence modeling**
- **Human‑readable explanations**
- **Graph‑based threat representation**
- **Ethical OSINT datasets**
- **Research‑friendly tooling**
- **Full STIX 2.1 interoperability** *(v0.3.0)*

### Core Principles

- **Public data only** — no private or sensitive information
- **Explainability first** — every risk score must be interpretable
- **Modular architecture** — easy to extend or replace
- **Research transparency** — datasets and logic are fully visible
- **Ethical OSINT** — aligned with academic and open‑source norms
- **Standard-first interoperability** — STIX 2.1 / TAXII 2.1 compliance means plug-and-play integration with the industry's leading platforms

---

## 🏗️ Repository Architecture

```
open-intelligence-lab/
├── datasets/
│   ├── threat_entities.json       # 21 entities: actors, malware, infra, CVEs, sectors
│   ├── attack_patterns.json       # 15 OSINT-specific attack patterns + MITRE mappings
│   ├── relations.json             # 28 directed graph edges
│   ├── mitre_mapping.json         # Actor → TTP frequency profiles
│   └── campaigns.json             # 7 campaigns (Diamond Model)
│
├── core_engine/
│   ├── graph_builder.py           # JSON → NetworkX DiGraph
│   ├── risk_analyzer.py           # Confidence-weighted risk scoring
│   └── explainability.py          # Plain-language rationale generation
│
├── api/
│   └── intelligence/router.py     # FastAPI REST API
│
├── backend/
│   ├── stix_exporter.py           # ★ v0.3.0 — STIX 2.1 bundle builder
│   └── taxii_server.py            # ★ v0.3.0 — TAXII 2.1 FastAPI server
│
├── visualization/
│   └── graph_visualizer.py        # NetworkX + Matplotlib graph rendering
│
├── exports/                       # ★ v0.3.0 — Generated STIX export files
│   ├── stix_bundle.json           # Raw STIX 2.1 bundle
│   ├── splunk_events.json         # Splunk ES format
│   ├── sentinel_indicators.json   # Microsoft Sentinel TI format
│   ├── opencti_bundle.json        # OpenCTI STIX 2.1 import
│   └── qradar_objects.json        # IBM QRadar STIX connector format
│
├── demo.py                        # End-to-end pipeline demo
├── index.html                     # Visual Lab (GitHub Pages)
└── README.md
```

---

## 🔌 v0.3.0 — STIX 2.1 Interoperability

### What's New

v0.3.0 migrates the internal dataset model to full **STIX 2.1** compliance and introduces a **TAXII 2.1** server layer. The platform is now natively interoperable with four of the industry's leading threat intelligence platforms.

| Platform | Integration Method | Format | Status |
|---|---|---|---|
| **Splunk Enterprise Security** | STIX-TAXII connector | STIX 2.1 events → Splunk index | ✅ Ready |
| **Microsoft Sentinel** | Threat Intelligence blade (TAXII) | STIX 2.1 indicator objects | ✅ Ready |
| **OpenCTI** | Native STIX 2.1 import | Raw STIX 2.1 bundle | ✅ Ready |
| **IBM QRadar SIEM** | STIX connector app | Flat STIX object list | ✅ Ready |

### STIX 2.1 Object Mapping

| OI Lab Entity Type | STIX 2.1 Object Type | Notes |
|---|---|---|
| `threat_actor` | `threat-actor` | Includes x_oi_risk_score extension |
| `malware` | `malware` | Capabilities, is_family fields populated |
| `infrastructure` | `infrastructure` | C2 and exploit targets |
| `vulnerability` (CVE) | `vulnerability` | NVD external reference auto-linked |
| `sector` | `identity` (class: sector) | STIX identity pattern for victim sectors |
| `attack_pattern` | `attack-pattern` | Kill chain + MITRE external reference |
| `campaign` | `campaign` | Diamond Model fields as x_ extensions |
| `relations.json` edges | `relationship` | Directed, confidence-weighted |

### Running the STIX Export

```bash
# Export all formats
python backend/stix_exporter.py

# Outputs written to exports/:
#   stix_bundle.json         — Raw STIX 2.1 (OpenCTI)
#   splunk_events.json       — Splunk ES sourcetype=stix
#   sentinel_indicators.json — Microsoft Sentinel TI blade
#   qradar_objects.json      — IBM QRadar flat objects

# Start TAXII 2.1 server
uvicorn backend.taxii_server:app --host 0.0.0.0 --port 8000

# TAXII endpoints:
#   GET /taxii/                                    — Discovery
#   GET /taxii/api-root/collections/               — List collections
#   GET /taxii/api-root/collections/{id}/objects/  — Get STIX objects
```

### TAXII 2.1 Collections

| Collection ID | Contents |
|---|---|
| `oi-lab-threat-actors-001` | Threat actor + identity objects |
| `oi-lab-attack-patterns-002` | MITRE-mapped attack patterns |
| `oi-lab-campaigns-003` | Diamond Model campaigns |
| `oi-lab-full-bundle-004` | Complete STIX 2.1 bundle |

### Connecting Splunk ES

1. In Splunk ES, navigate to **Configure → Threat Intelligence → Intelligence Downloads**
2. Add a new TAXII source: `http://your-server:8000/taxii/`
3. Select collection `oi-lab-full-bundle-004`
4. Set polling interval (recommended: 1 hour for a research feed)

### Connecting Microsoft Sentinel

1. In Sentinel, open **Threat Intelligence → TAXII (Preview)**
2. Add connector: `http://your-server:8000/taxii/api-root/`
3. Collection: `oi-lab-threat-actors-001` or `oi-lab-full-bundle-004`
4. Indicators appear in the **ThreatIntelligenceIndicator** table

### Connecting OpenCTI

1. Navigate to **Data → Import**
2. Select **STIX 2.1** import connector
3. Upload `exports/opencti_bundle.json` directly, or point the TAXII connector at the server

### Connecting IBM QRadar

1. Install the **STIX Threat Intelligence** app from IBM App Exchange
2. Configure the TAXII feed: `http://your-server:8000/taxii/api-root/`
3. Map `oi_risk_score` to QRadar's offense magnitude field

---

## 🧩 System Architecture

```
flowchart TD
    subgraph Datasets
        TE[threat_entities.json]
        AP[attack_patterns.json]
        RL[relations.json]
        MM[mitre_mapping.json]
        CA[campaigns.json]
    end

    subgraph CoreEngine
        GB[graph_builder.py]
        RA[risk_analyzer.py]
        EX[explainability.py]
    end

    subgraph STIXLayer ["STIX 2.1 Layer (v0.3.0)"]
        SE[stix_exporter.py]
        TX[taxii_server.py]
    end

    subgraph Platforms
        SP[Splunk ES]
        SN[Microsoft Sentinel]
        OC[OpenCTI]
        QR[IBM QRadar]
    end

    subgraph API
        IA[intelligence/router.py]
    end

    TE & AP & RL & MM & CA --> GB
    GB --> RA --> EX
    GB & RA --> SE
    SE --> TX
    TX --> SP & SN & OC & QR
    GB & RA & EX --> IA
```

---

## 📊 Dataset Overview

| File | Count | Description |
|---|---|---|
| `threat_entities.json` | 21 entities | Actors, malware, infra, CVEs, sectors |
| `attack_patterns.json` | 15 patterns | OSINT ATT&CK-mapped techniques |
| `relations.json` | 28 edges | Directed confidence-weighted relationships |
| `mitre_mapping.json` | 21 mappings | Actor → TTP frequency |
| `campaigns.json` | 7 campaigns | Diamond Model intrusion records |

---

## 🔬 Risk Scoring Model

```
Risk Score = (Threat Likelihood × CIA Impact) × Confidence Weight
             clamped to [0.0, 1.0] → LOW / MEDIUM / HIGH / CRITICAL
```

Every score triggers `explainability.py`, which generates a plain-language rationale string at computation time. No score is ever a naked number.

---

## 🗺️ Roadmap

| Version | Focus |
|---|---|
| v0.1.0 ✅ | Core graph engine, datasets, API, visual lab |
| v0.2.0 | FastAPI backend live; demo.py → service.py wiring |
| **v0.3.0 ✅** | **STIX 2.1 export, TAXII 2.1 server, Splunk/Sentinel/OpenCTI/QRadar interop** |
| v0.4.0 | MISP integration, TAXII feed ingestion with provenance |
| v1.0.0 | Neo4j backend, ML-assisted scoring with SHAP explainability |

---

## 📎 Links

- **Visual Lab**: [alborznazari.github.io/open-intelligence-lab](https://alborznazari.github.io/open-intelligence-lab/)
- **Medium Article**: [Open Intelligence Lab on git](https://medium.com/@alborznazari4/open-intelligence-lab-on-git-from-a-black-box-to-a-transparent-modular-and-open-source-model-ffa154962964)
- **STIX 2.1 Spec**: [oasis-open.github.io/cti-documentation](https://oasis-open.github.io/cti-documentation/stix/intro)
- **TAXII 2.1 Spec**: [docs.oasis-open.org/cti/taxii](https://docs.oasis-open.org/cti/taxii/v2.1/os/taxii-v2.1-os.html)

---

## License

MIT License — see [LICENSE](LICENSE) for details.

*Open Intelligence Lab — public data, open reasoning, interpretable results.*
