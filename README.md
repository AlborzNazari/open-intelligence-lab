# Open Intelligence Lab

[![Research Status](https://img.shields.io/badge/research-alpha-blue)](https://github.com/AlborzNazari/open-intelligence-lab)
[![Dataset Version](https://img.shields.io/badge/datasets-v0.1-green)](https://github.com/AlborzNazari/open-intelligence-lab/tree/main/datasets)
[![Model Version](https://img.shields.io/badge/intelligence_model-v0.1-orange)](https://github.com/AlborzNazari/open-intelligence-lab)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![MITRE ATT&CK](https://img.shields.io/badge/MITRE-ATT%26CK%20Aligned-red)](https://attack.mitre.org/)

**Open Intelligence Lab** is an ethical OSINT research platform focused on public-security intelligence representation, graph-based threat modeling, and explainable risk analytics.

It provides a clean, modular environment for researchers, analysts, and engineers who want to explore open-source intelligence signals **without compromising privacy or ethics** — using only public data, with every risk score backed by an interpretable rationale.

> 📖 Read the full article: [From a Black Box to a Transparent, Modular, and Open-Source Model](https://medium.com/@alborznazari4/open-intelligence-lab-on-git-from-a-black-box-to-a-transparent-modular-and-open-source-model-ffa154962964)

---

## What Does This Software Do?

Open Intelligence Lab models real-world threat intelligence as a **traversable knowledge graph**:

- **21 entities** — threat actors (APT28, APT29, APT41, Lazarus, LockBit, Cl0p, KillNet), malware families, CVEs, infrastructure nodes, and target sectors
- **28 documented relations** — `uses`, `exploits`, `targets`, `uses_pattern`, `related_to`
- **7 real campaigns** — SolarWinds, MOVEit, LockBit 3.0, Bybit Heist, and more
- **Risk scoring** — every entity gets a score from 0.0 to 1.0 computed from threat likelihood × impact × confidence, bucketed into `LOW / MEDIUM / HIGH / CRITICAL`
- **Explainability** — every risk score produces a plain-language rationale, never a naked number
- **MITRE ATT&CK alignment** — all actors and patterns are mapped to official technique IDs

Run `demo.py` and an **interactive browser dashboard** opens showing the full threat knowledge graph — click any node to inspect its risk score, confidence, connections, and intelligence rationale.

---

## Repository Architecture

```
open-intelligence-lab/
├── demo.py                    ← Entry point — runs the full pipeline
├── index.html                 ← Project documentation site
│
├── datasets/                  ← 5 JSON knowledge base files
│   ├── threat_entities.json   ← 21 entities (actors, malware, CVEs, sectors, infra)
│   ├── attack_patterns.json   ← 15 OSINT attack patterns with MITRE mappings
│   ├── relations.json         ← 28 directed edges (the graph lives here)
│   ├── campaigns.json         ← 7 real-world campaigns (Diamond Model)
│   └── mitre_mapping.json     ← ATT&CK technique profiles per actor
│
├── core_engine/               ← Intelligence pipeline
│   ├── graph_builder.py       ← Builds DiGraph from datasets (NetworkX)
│   ├── risk_analyzer.py       ← Risk = Likelihood × Impact × Confidence
│   ├── intelligence_explainer.py ← Plain-language rationale generator
│   └── intelligence_entities.py  ← Entity data model
│
├── visualization/
│   └── graph_renderer.py      ← Interactive browser graph (Canvas + D3-style)
│
├── api/
│   ├── main.py                ← FastAPI app entry point
│   └── intelligence/
│       ├── router.py          ← GET /intelligence/risk/{entity_id}
│       ├── service.py         ← Pipeline orchestration
│       └── schemas.py         ← Pydantic response models
│
└── backend/
    └── requirements.txt       ← API/server dependencies
```
<img width="928" height="916" alt="Medium_02" src="https://github.com/user-attachments/assets/769d41e7-2bca-4b4b-978b-01c58a1e095b" />

---

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

---

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

---

## Running the API

```bash
uvicorn api.main:app --reload --port 8000
```

Then open:
- **Interactive docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Risk endpoint:** `http://localhost:8000/intelligence/risk/{entity_id}`

Example:
```bash
curl http://localhost:8000/intelligence/risk/TA-001
```

---

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

Every score is accompanied by a plain-language rationale. No risk score is ever a naked number.

---

## Datasets

All data is sourced from **public, ethical sources only**:

| File | Contents | Source |
|------|----------|--------|
| `threat_entities.json` | 21 entities across 5 types | MITRE ATT&CK, CISA Advisories |
| `attack_patterns.json` | 15 OSINT attack patterns | MITRE ATT&CK, public research |
| `relations.json` | 28 directed edges | MITRE ATT&CK, CISA, Mandiant |
| `campaigns.json` | 7 campaigns (Diamond Model) | Public threat reports |
| `mitre_mapping.json` | TTP profiles per actor | MITRE ATT&CK |

---

## Core Principles

- **Public data only** — no private, scraped, or sensitive information
- **Explainability first** — every risk score must be traceable and expressible in plain language
- **Modular architecture** — each layer can be replaced or extended independently
- **Research transparency** — datasets, scoring logic, and relationships are fully visible
- **Ethical OSINT** — aligned with academic norms and MITRE ATT&CK attribution standards

---

## Roadmap

- **v0.2** — STIX 2.1 schema compliance, TAXII feed integration
- **v0.3** — Neo4j backend for multi-hop actor pivoting at scale
- **v1.0** — ML-based risk scoring with SHAP explainability, OpenCTI/MISP integration

---

## Contributing

Contributions are welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md) and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before submitting a pull request.

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

*Open Intelligence Lab · Alborz Nazari · 2026 · [medium.com/@alborznazari4](https://medium.com/@alborznazari4)*
