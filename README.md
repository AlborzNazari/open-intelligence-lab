## 🌐 Live Demo

> **[▶ Open Intelligence Lab — Live Web App](https://alborznazari.github.io/open-intelligence-lab/)**


# Open Intelligence Lab

![Research Status](https://img.shields.io/badge/research-alpha-blue)
![Dataset Version](https://img.shields.io/badge/datasets-v0.1-green)
![Model Version](https://img.shields.io/badge/intelligence_model-v0.1-orange)


<img width="928" height="916" alt="Medium_02" src="https://github.com/user-attachments/assets/617c605d-4140-40e2-a745-b0a992df88a4" />


Open Intelligence Lab is an ethical OSINT research platform focused on public‑security intelligence representation, graph‑based threat modeling, and explainable risk analytics.  
It provides a clean, modular environment for researchers, analysts, and engineers who want to explore open‑source intelligence signals **without compromising privacy or ethics**.


### Core Principles


**No harm clause
This software may not be used to harass, intimidate, stalk, profile, target, or otherwise harm any individual or group.**
**No doxxing or exposure
The database, models, or derived intelligence may not be used to expose personal information, correlate identities for harassment, or facilitate real-world targeting.**
**No unlawful surveillance
This project may not be used to conduct unauthorized monitoring, tracking, or surveillance activities.**
**Defensive and research use only
The intended use cases are academic research, defensive security analysis, transparency research, and educational experimentation.**
**No automated punitive decisions
Outputs from this system must not be used as sole justification for banning, blacklisting, firing, prosecuting, or otherwise penalizing individuals or entities without human review and external verification.**


## 🧠 Vision & Philosophy

**Security intelligence is often opaque, proprietary, and difficult to interpret.  
This project aims to change that by offering:**

- **Transparent intelligence modeling**  
- **Human‑readable explanations**  
- **Graph‑based threat representation**  
- **Ethical OSINT datasets**  
- **Research‑friendly tooling**


# 🏗️ Repository Architecture

Below is a high‑level overview of how the system works.

---

## 🧩 System Architecture 

```mermaid
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



