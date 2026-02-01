# Progressive Delivery for Agents: Shadow, Canary, Rollback

Sample code for the article "Progressive Delivery for Agents: Shadow Tests, Eval Gates, and Fast Rollbacks."

## Overview

This repo includes:

- **Trace format (JSONL)** – One JSON object per line: `trace_id`, `request`, `tool_calls`, `tool_results`, `response`, `outcome`, `latency_ms`, `cost_tokens`.
- **Python replay script** – Loads traces, replays them against two agent versions (baseline vs candidate), and prints a pass/fail summary (success, tool misuse, budget overruns).
- **GitHub Actions workflow** – Runs unit tests, offline eval suite, and a quality gate that blocks merge if thresholds fail.
- **Feature-flagged router** – Supports shadow execution, canary percentage rollout, and instant rollback.
- **OpenTelemetry snippet** – Minimal spans for `agent.run`, `agent.step`, `tool.call`, `tool.result`.

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

### Load and replay traces

```bash
# Replay fixtures against baseline and candidate; print pass/fail summary
python -m src.replay \
  --traces tests/fixtures/sample_traces.jsonl \
  --baseline-version v1 \
  --candidate-version v2 \
  --max-latency-ms 2000 \
  --max-cost-tokens 800
```

### Run unit tests

```bash
pytest tests/ -v
```

### Run offline eval (quality gate)

```bash
python scripts/run_eval_gate.py
# Exits 0 if pass, 1 if fail (for CI)
```

### Router (shadow / canary / rollback)

See `src/router.py` for a minimal feature-flagged router. Use `mode=shadow`, `mode=canary` with `canary_percent`, or `mode=baseline` for full rollback.

## Layout

```
.
├── src/
│   ├── __init__.py
│   ├── trace_loader.py   # Load JSONL traces
│   ├── replay.py         # Replay traces, compare versions, pass/fail summary
│   ├── router.py         # Shadow / canary / rollback router
│   └── observability.py  # OpenTelemetry spans (agent_step, tool_call, tool_result)
├── tests/
│   ├── test_trace_loader.py
│   ├── test_replay.py
│   ├── test_router.py
│   └── fixtures/
│       └── sample_traces.jsonl
├── scripts/
│   └── run_eval_gate.py  # CI quality gate
├── .github/
│   └── workflows/
│       └── ci.yml        # Unit tests + offline eval + quality gate
├── requirements.txt
├── pytest.ini
└── README.md
```

## Trace format (JSONL)

Each line is a JSON object:

```json
{"trace_id": "tr_001", "request": "What's our refund policy?", "tool_calls": [{"name": "search_docs", "args": {"query": "refund"}}], "tool_results": [{"success": true, "result": {"docs": [...]}}], "response": "Our refund policy is...", "outcome": "success", "latency_ms": 1200, "cost_tokens": 500}
```

Fields used by the replay script: `trace_id`, `request`, `tool_calls`, `tool_results`, `response`, `outcome`, `latency_ms`, `cost_tokens`. Optional: `allowed_tools`, `expected_outcome`.

## License

MIT.
