# Open Intelligence Lab

Open Intelligence Lab is an ethical OSINT research platform focused on public security intelligence representation, graph-based threat knowledge modeling, and explainable security analytics.

![Research Status](https://img.shields.io/badge/research-alpha-blue)
![Dataset Version](https://img.shields.io/badge/datasets-v0.1-green)
![Intelligence Model Version](https://img.shields.io/badge/model-v0.1-orange)

## Core focus

- Threat knowledge graph (entities, relations, attack patterns)
- Public OSINT dataset contribution (metadata-level only)
- Visualization + explanation layer for human-readable security insight

> This project does not collect private or sensitive personal information.  
> Only public, ethically sourced security intelligence is in scope.

## High-level architecture

- `datasets/` — local research datasets (entities, attack patterns, relations)
- `core_engine/` — graph builder, risk analyzer, explanation layer
- `visualization/` — graph and dashboard visualizations
- `api/` — simple intelligence API (future-friendly)
- `research_docs/` — notes, methodology, experiments
