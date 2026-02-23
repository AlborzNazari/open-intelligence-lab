# Open Intelligence Lab

![Research Status](https://img.shields.io/badge/research-alpha-blue)
![Dataset Version](https://img.shields.io/badge/datasets-v0.1-green)
![Model Version](https://img.shields.io/badge/intelligence_model-v0.1-orange)

Open Intelligence Lab is an ethical OSINT research platform focused on public security intelligence representation, graph‑based threat knowledge modeling, and explainable security analytics.  
The project provides a structured environment for researchers, analysts, and engineers who want to explore open‑source intelligence signals without compromising privacy or ethical standards.


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

## 🧩 System Architecture (Mermaid Diagram)

flowchart TD

    %% ===========================
    %% DATASETS
    %% ===========================
    subgraph Datasets
        TE[threat_entities.json]
        AP[attack_patterns.json]
        RL[relations.json]
    end

    %% ===========================
    %% CORE ENGINE
    %% ===========================
    subgraph CoreEngine
        GB[graph_builder.py]
        RA[risk_analyzer.py]
        EX[explainability.py]
    end

    %% ===========================
    %% VISUALIZATION
    %% ===========================
    subgraph Visualization
        GV[graph_visualizer.py]
        DB[dashboards]
    end

    %% ===========================
    %% API LAYER
    %% ===========================
    subgraph API
        IA[intelligence/router.py]
    end

    %% ===========================
    %% RESEARCH OUTPUT
    %% ===========================
    subgraph Research
        RD[research_docs/]
    end

    %% DATA → GRAPH
    TE --> GB
    AP --> GB
    RL --> GB

    %% GRAPH → ANALYSIS
    GB --> RA
    RA --> EX

    %% GRAPH → VISUALIZATION
    GB --> GV
    RA --> GV
    EX --> GV

    %% ENGINE → API
    GB --> IA
    RA --> IA
    EX --> IA

    %% API → RESEARCH
    IA --> RD


# Open Intelligence Lab  
A beginner‑friendly, modular framework for learning and experimenting with **OSINT**, **graph‑based intelligence**, and **explainable risk analysis**.

This project is designed so even junior developers can understand how intelligence systems work step‑by‑step.  
Everything is built in small, simple modules you can explore, modify, and learn from.

## 🌱 What This Project Is (In Simple Words)

This project helps you:

- Load simple public‑data examples (OSINT‑style)
- Build a **graph** of entities (people, orgs, attacks, etc.)
- Analyze relationships and detect patterns
- Compute simple **risk scores**
- Visualize the graph
- Access everything through a small **API**

## ⚙️ Installation


---

## 🧰 Requirements

- Python 3.10 or newer  
- pip (Python package installer)

---

## 🚀 Getting Started (Super Easy)

### 1. Clone the project

```bash
git clone https://github.com/AlborzNazari/open-intelligence-lab.git
cd open-intelligence-lab


### 1. Create a virtual environment (recommended)

python -m venv venv
venv\Scripts\activate
source venv/bin/activate
pip install -r requirements.txt


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
