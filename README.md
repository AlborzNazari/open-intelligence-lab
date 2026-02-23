# Open Intelligence Lab

![Research Status](https://img.shields.io/badge/research-alpha-blue)
![Dataset Version](https://img.shields.io/badge/datasets-v0.1-green)
![Model Version](https://img.shields.io/badge/intelligence_model-v0.1-orange)

Open Intelligence Lab is an ethical OSINT research platform focused on public security intelligence representation, graph‑based threat knowledge modeling, and explainable security analytics.  
The project provides a structured environment for researchers, analysts, and engineers who want to explore open‑source intelligence signals without compromising privacy or ethical standards.

---

## 🧠 Vision & Philosophy

Security intelligence is often siloed, opaque, and difficult to interpret.  
This project aims to change that by offering:

- **Transparent intelligence modeling**  
- **Human‑readable explanations**  
- **Graph‑based threat representation**  
- **Ethical OSINT dataset contribution**  
- **Research‑friendly tooling**  

The goal is not to replicate existing threat‑intel platforms, but to create a **lightweight, open, explainable research lab** that anyone can build upon.

### Core Principles

- **Public data only** — no private or sensitive information  
- **Explainability first** — every risk score must be interpretable  
- **Modular architecture** — easy to extend, replace, or integrate  
- **Research transparency** — datasets and logic are fully visible  
- **Ethical OSINT** — aligned with academic and open‑source norms  

---

## 🏗️ Repository Architecture

open-intelligence-lab/
│
├── datasets/
│   ├── threat_entities/        # Organizations, domains, categories
│   ├── attack_patterns/        # Local OSINT attack pattern taxonomy
│   └── relations/              # Entity-to-entity relationship data
│
├── core_engine/
│   ├── graph_builder.py        # Knowledge graph construction
│   ├── risk_analyzer.py        # Risk scoring logic
│   ├── intelligence_explainer.py # Explainable intelligence layer
│   └── intelligence_entities.py # Entity schema definitions
│
├── visualization/
│   ├── graph_renderer.py       # Network graph visualization
│   └── dashboard/              # (Future) interactive dashboards
│
├── api/
│   └── intelligence_api.py     # Lightweight API for intelligence queries
│
├── research_docs/              # Notes, methodology, experiments
│
└── README.md


This structure follows clean‑architecture principles:  
**data → core logic → visualization → API → research documentation**.

---

## ⚙️ Installation

### 1. Create a virtual environment (recommended)

```bash
python3 -m venv venv
source venv/bin/activate
2. Install dependencies
Using requirements.txt:

bash
pip install -r requirements.txt
Or install manually:

bash
pip install networkx fastapi uvicorn matplotlib

bash
python demo.py

uvicorn api.intelligence_api:app --reload

Then open:

http://127.0.0.1:8000/entities/org:1/explanation

Risk Score: 0.72
- Entity appears in multiple public reports
- Connected to incident categories with elevated risk
- Graph connectivity indicates increased exposure


---
