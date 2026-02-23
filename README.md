# Open Intelligence Lab

![Research Status](https://img.shields.io/badge/research-alpha-blue)
![Dataset Version](https://img.shields.io/badge/datasets-v0.1-green)
![Model Version](https://img.shields.io/badge/intelligence_model-v0.1-orange)

Open Intelligence Lab is an ethical OSINT research platform focused on public security intelligence representation, graph‑based threat knowledge modeling, and explainable security analytics.  
The project provides a structured environment for researchers, analysts, and engineers who want to explore open‑source intelligence signals without compromising privacy or ethical standards.

##
   ____                 ___       _       _             
  / __ \___  ___  ____ / (_)___  (_)___  (_)___  ____ _
 / / / / _ \/ _ \/ __ `/ / / __ \/ / __ \/ / __ \/ __ `/
/ /_/ /  __/  __/ /_/ / / / / / / / / / / / / / / /_/ / 
\____/\___/\___/\__,_/_/_/_/ /_/_/_/ /_/_/_/ /_/\__,_/  
                                                        
      Open Intelligence Lab
      Ethical • Explainable • Graph‑Based OSINT


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

    subgraph Datasets
        TE[threat_entities]
        AP[attack_patterns]
        RL[relations]
    end

    subgraph CoreEngine
        GB[graph_builder.py]
        RA[risk_analyzer.py]
        IE[intelligence_explainer.py]
        EN[intelligence_entities.py]
    end

    subgraph Visualization
        GR[graph_renderer.py]
        DB[dashboard]
    end

    subgraph API
        IA[intelligence_api.py]
    end

    subgraph Research
        RD[research_docs]
    end

    TE --> GB
    AP --> GB
    RL --> GB

    GB --> RA
    RA --> IE

    GB --> GR
    RA --> GR
    IE --> GR

    IE --> IA
    RA --> IA
    GB --> IA

    IA --> RD


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
