# Agentic Shadow Models — Reducing Latency via Local Predictive Replicas

This repo accompanies the article **"Agentic Shadow Models — Reducing Latency via Local Predictive Replicas"**.
It provides a practical scaffold for building local predictive replicas (shadows) of peer agents to reduce
coordination latency while tracking confidence and drift.

## Features
- `Planner` and `Executor` agents with a simple protocol.
- `ShadowModel` that learns to approximate the Executor's responses using scikit-learn.
- Confidence monitoring and fallback to live Executor when confidence is low.
- Offline-friendly sample dataset & demo.
- PyTest tests.

## Quickstart
```bash
python -m venv .venv && source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
python examples/demo_shadow_vs_live.py
pytest -q
```

## Mermaid Diagram (Hero)
```mermaid
graph LR
A[Planner Agent] --> B[Shadow Model (Predictive Replica)]
B --> C[Executor Agent]
B --> D[Confidence Monitor]
D --> A
C --> E[Feedback Loop for Shadow Update]
E --> B
```

## Repo Layout
```
agentic-shadow-models/
  ├─ LICENSE
  ├─ requirements.txt
  ├─ .gitignore
  ├─ README.md
  ├─ data/
  │   └─ sample_executor_pairs.jsonl
  ├─ src/
  │   ├─ agents.py
  │   ├─ shadow.py
  │   └─ monitor.py
  ├─ examples/
  │   └─ demo_shadow_vs_live.py
  └─ tests/
      └─ test_shadow.py
```
