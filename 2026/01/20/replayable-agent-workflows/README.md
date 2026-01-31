# Replayable Agent Workflows: Checkpoints, Time-Travel, and Regression Tests

A complete Python implementation demonstrating how to make agents reproducible with checkpoints, time-travel debugging, and regression tests from production runs.

## Overview

This repository shows how to:
- Emit events for every agent step
- Store checkpoints with full state
- Record and replay tool calls
- Resume from any checkpoint
- Fork runs with modified state
- Turn production incidents into regression tests
- Add OpenTelemetry instrumentation

## Features

- **Event-Driven Architecture**: Every step emits an event with input/output state
- **Checkpoint Store**: SQLite + JSON for metadata and payloads
- **Tool Recording**: Record tool calls and replay from fixtures
- **Time-Travel Debugging**: Resume from checkpoint, fork state, compare outcomes
- **Regression Tests**: Turn production runs into pytest tests
- **OpenTelemetry**: Traces per run, spans per step/tool

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

### 1. Run Agent with Checkpointing

```bash
python examples/run_agent.py --query "What's the weather in San Francisco?"
```

This will:
- Execute agent with tool calls
- Emit events for each step
- Store checkpoints in SQLite
- Record tool results
- Print run_id for replay

### 2. Replay a Run

```bash
python examples/replay_run.py --run-id <run_id>
```

This will:
- Load events from checkpoint store
- Replay state transitions
- Use recorded tool results (no re-execution)
- Print step-by-step execution

### 3. Time-Travel Debug

```bash
python examples/time_travel.py --run-id <run_id> --step-id step_3 --modify '{"max_retries": 3}'
```

This will:
- Load checkpoint at step 3
- Apply state modifications
- Continue execution from there
- Compare with original run

### 4. Run Regression Tests

```bash
pytest tests/test_regression.py
```

This will:
- Load golden traces from production
- Replay each trace
- Assert tool sequences match
- Assert intermediate states match
- Assert expected outcomes

## Project Structure

```
.
├── src/
│   ├── agent.py                    # Minimal agent with step boundaries
│   ├── checkpoint_store.py         # Checkpoint storage (SQLite + JSON)
│   ├── tool_recorder.py            # Record/replay tool wrapper
│   ├── time_travel.py              # Resume, fork, compare runs
│   ├── events.py                   # Event definitions
│   └── observability.py            # OpenTelemetry instrumentation
├── examples/
│   ├── run_agent.py                # Run agent with checkpointing
│   ├── replay_run.py               # Replay a recorded run
│   ├── time_travel.py              # Time-travel debugging
│   └── incident_response.py        # Handle production incident
├── fixtures/
│   ├── tool_recordings/            # Recorded tool calls
│   └── golden_traces/              # Production runs as tests
├── tests/
│   ├── test_checkpoint_store.py    # Unit tests for checkpoint store
│   ├── test_tool_recorder.py       # Unit tests for tool recorder
│   ├── test_time_travel.py         # Unit tests for time-travel
│   └── test_regression.py          # Regression tests from production
├── requirements.txt
├── pytest.ini
└── README.md
```

## How It Works

### Event-Driven Agent

The agent emits an event for every step:

```python
class StepEvent:
    step_id: str
    input_state: dict
    decision: str
    tool_name: str
    tool_args: dict
    tool_result: dict
    output_state: dict
    timestamp: datetime
```

Each event captures everything needed to reproduce that step.

### Checkpoint Store

Checkpoints are stored in two places:
- **SQLite**: Metadata (run_id, step_id, timestamp, agent_version)
- **JSON files**: Large payloads (messages, tool_calls, state)

```python
checkpoint_store.save_checkpoint(checkpoint)
checkpoint = checkpoint_store.load_checkpoint(run_id, step_id)
```

### Tool Recording

Tools are wrapped to record inputs and outputs:

```python
@record_tool
def search_docs(query: str) -> dict:
    # Real implementation
    return {"docs": [...]}
```

During replay, recorded results are used instead of re-executing:

```python
replayer = ToolReplayer(run_id)
result = replayer.replay("search_docs", {"query": "..."})
```

### Time-Travel Debugging

Resume from any checkpoint:

```python
# Resume from step 5
result = resume_from_checkpoint(run_id, "step_5")

# Fork with modified state
fork_id, result = fork_run(run_id, "step_5", {"max_retries": 3})

# Compare where they diverged
divergence = compare_runs(run_id, fork_id)
```

## Examples

### Example 1: Agent Gets Stuck in Loop

See `examples/incident_response.py` for a complete walkthrough:

1. Agent gets stuck calling `search_docs` repeatedly
2. Replay the run to see the loop
3. Inspect tool results (all empty)
4. Fork with fix (add empty result check)
5. Compare original vs fork
6. Add regression test
7. Deploy fix

### Example 2: Tool Returns Unexpected Result

See `examples/time_travel.py`:

1. Agent fails at step 7
2. Load checkpoint at step 6
3. Inspect state before failure
4. Fork with different tool args
5. See if it succeeds
6. Identify root cause

### Example 3: Non-Deterministic Behavior

See `tests/test_regression.py`:

1. Production run produces wrong answer
2. Save as golden trace
3. Replay with recorded tool results
4. Assert tool sequence matches
5. Assert intermediate states match
6. Catch regressions in future changes

## Code Samples

### 1. Minimal Agent Graph

See `src/agent.py` for:
- Agent with step boundaries
- Event emission per step
- Tool call recording
- State management

### 2. Checkpoint Store

See `src/checkpoint_store.py` for:
- Interface definition
- SQLite + JSON implementation
- Redaction for PII/secrets
- Retention policies

### 3. Tool Recorder/Replayer

See `src/tool_recorder.py` for:
- Tool wrapper that records calls
- Fixture-based replay
- Deterministic tool execution
- Idempotent side effects

### 4. Time-Travel Runner

See `src/time_travel.py` for:
- Resume from checkpoint
- Fork with state modifications
- Compare run divergence
- Diff tool sequences

### 5. Regression Test Harness

See `tests/test_regression.py` for:
- Load golden traces
- Replay with assertions
- Tool sequence validation
- State snapshot testing
- Expected outcome verification

### 6. OpenTelemetry Instrumentation

See `src/observability.py` for:
- Trace per run
- Span per step
- Span per tool call
- GenAI semantic conventions
- Error tracking

## Testing

Run all tests:

```bash
pytest
```

Run with coverage:

```bash
pytest --cov=src --cov-report=html
```

Run specific test:

```bash
pytest tests/test_checkpoint_store.py -v
```

Run regression tests only:

```bash
pytest tests/test_regression.py -v
```

## Incident Response Workflow

When a production incident occurs:

1. **Locate run_id**: Find in logs or user report
2. **Replay**: `python examples/replay_run.py --run-id <run_id>`
3. **Inspect**: Look at events, tool results, state transitions
4. **Fork**: `python examples/time_travel.py --run-id <run_id> --step-id <step> --modify '{...}'`
5. **Compare**: See where behavior diverged
6. **Test**: Add golden trace to `fixtures/golden_traces/`
7. **Fix**: Update agent code
8. **Verify**: Run regression tests
9. **Deploy**: Ship fix with confidence

## Best Practices

1. **Event Emission**: Emit events for every step, not just tool calls
2. **Checkpoint Storage**: Use DB for metadata, blob store for payloads
3. **Redaction**: Redact PII and secrets before storing
4. **Retention**: Keep failed runs longer than successful runs
5. **Idempotency**: Make side effects idempotent
6. **Tool Separation**: Separate read tools from write tools
7. **Recording**: Record all non-deterministic operations
8. **Observability**: Add OpenTelemetry traces
9. **Testing**: Turn production incidents into regression tests
10. **Cost Control**: Sample checkpoints, compress payloads, store deltas

## Metrics

Track these metrics in production:
- **Checkpoint success rate**: Percentage of runs successfully checkpointed
- **Replay success rate**: Percentage of replays that complete
- **Storage size**: Total checkpoint storage used
- **Replay latency**: Time to replay a run
- **Divergence rate**: Percentage of forks that diverge from original

## License

This code is provided as example code for educational purposes.
