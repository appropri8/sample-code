# Agent Observability with OpenTelemetry Traces

A complete example showing how to instrument AI agents with OpenTelemetry traces for observability, evaluation, and debugging.

## Overview

This repository demonstrates:

- **Instrumented Agent Loop**: Python agent with OpenTelemetry spans for LLM calls, tool calls, and decisions
- **OTel Collector Config**: Minimal config to export traces to console and OTLP endpoint
- **Eval from Traces Script**: Reads exported traces (JSON), computes 6 metrics (completion rate, tool error rate, cost, loops, time to first output, wasted steps)
- **Redaction Helper**: Removes secrets/PII from span attributes using deny-list patterns
- **Bad Run Fixture**: Example trace showing a failed run with loops and errors

## Features

- ✅ Full OpenTelemetry instrumentation for agent runs
- ✅ Spans for LLM calls, tool calls, and decisions
- ✅ Standardized attributes for evaluation
- ✅ PII/secret redaction
- ✅ Lightweight eval pipeline from traces
- ✅ Bad run detection (loops, errors, wasted steps)
- ✅ Cost tracking per run
- ✅ Time-to-first-output metrics

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

### 1. Run an Agent Task

```bash
python examples/run_agent.py
```

This will run a few agent tasks and generate traces. Traces are exported to console by default.

### 2. Test Redaction

```bash
python examples/test_redaction.py
```

This demonstrates how PII and secrets are redacted from span attributes.

### 3. Evaluate Traces

```bash
# First, test with the bad run fixture
python examples/test_eval.py

# Or evaluate your own traces (after exporting to JSON)
python src/eval_from_traces.py fixtures/bad_run_trace.json
```

## Project Structure

```
.
├── src/
│   ├── agent.py              # Instrumented agent loop
│   ├── redaction.py          # PII/secret redaction helper
│   └── eval_from_traces.py   # Eval pipeline from traces
├── examples/
│   ├── run_agent.py          # Example: Run agent tasks
│   ├── test_redaction.py     # Example: Test redaction
│   └── test_eval.py          # Example: Test eval with bad run
├── fixtures/
│   └── bad_run_trace.json    # Example bad run trace
├── otel-collector-config.yaml # OTel Collector configuration
├── requirements.txt
└── README.md
```

## Code Samples

### 1. Instrumented Agent Loop

The `src/agent.py` file shows:

- Root span for agent runs with attributes (task, user_id, workspace_id)
- LLM call spans with token counts, latency, cost
- Tool call spans with status, latency, error handling
- Decision spans for planning steps
- Proper span hierarchy (parent-child relationships)

```python
from src.agent import run_agent

result = run_agent(
    task="Analyze the code in src/main.py",
    user_id="user-123",
    workspace_id="workspace-456"
)
```

### 2. OTel Collector Config

The `otel-collector-config.yaml` file shows:

- OTLP receiver (gRPC and HTTP)
- Batch processor for efficiency
- Console exporter for development
- File exporter for JSON traces
- OTLP exporter for production backends

To use:

```bash
# Install OTel Collector
# https://opentelemetry.io/docs/collector/getting-started/

# Run collector
otelcol --config=otel-collector-config.yaml
```

### 3. Eval from Traces

The `src/eval_from_traces.py` script computes:

- **Tool Success Rate**: Per-tool success/error rates
- **Completion Rate**: How many runs completed successfully
- **Wasted Steps**: Loops and repeated tool calls
- **Time to First Output**: Latency until first useful result
- **Cost Per Run**: Total LLM costs
- **Tool Error Count**: Errors per run

```bash
python src/eval_from_traces.py traces.json
```

Output includes a metrics table and JSON file.

### 4. Redaction Helper

The `src/redaction.py` file provides:

- Deny-list patterns for common secrets (API keys, passwords, emails, SSNs)
- Recursive redaction for nested structures
- Safe attribute setting that redacts before export

```python
from src.redaction import set_attribute_safe

# Automatically redacts PII/secrets
set_attribute_safe(span, "user.email", "user@example.com")
set_attribute_safe(span, "api.key", "sk-1234567890abcdef")
```

### 5. Bad Run Fixture

The `fixtures/bad_run_trace.json` file shows:

- A failed run (max iterations reached)
- Multiple tool errors
- Repeated tool calls (read_file called 3+ times)
- High tool call count for a failed run

Use this to test your eval pipeline and understand what makes a run "bad".

## Standard Attributes

The code uses consistent attribute names:

**Run-level:**
- `agent.task`: Task description
- `agent.task_type`: Category (code_analysis, data_extraction, etc.)
- `agent.user_id`, `agent.workspace_id`, `agent.job_id`: Identifiers
- `agent.completed`: Boolean completion status
- `agent.final_state`: Terminal state (success, failure, timeout)

**LLM:**
- `llm.model`: Model name
- `llm.tokens_input`, `llm.tokens_output`, `llm.tokens_total`: Token counts
- `llm.latency_ms`: Call latency
- `llm.cost_estimate`: Estimated cost

**Tool:**
- `tool.name`: Tool name
- `tool.status`: "success" or "error"
- `tool.latency_ms`: Call latency
- `tool.error`: Error message if failed

**Decision:**
- `decision.type`: Type of decision
- `decision.selected`: What was selected
- `decision.reasoning`: Brief reasoning

## Metrics Table Example

Here are metrics for 3 sample runs:

| Run ID | Completed | Cost ($) | Tool Calls | Tool Errors | Time to Output (ms) | Wasted Steps |
|--------|-----------|----------|------------|-------------|---------------------|--------------|
| run-001 | Yes | 0.023 | 8 | 0 | 1,250 | 0 |
| run-002 | No | 0.045 | 15 | 3 | 2,100 | 2 (read_file repeated) |
| run-003 | Yes | 0.012 | 5 | 0 | 890 | 0 |

Run 002 shows a failure with high tool call count, errors, and wasted steps.

## Production Setup

### 1. Configure OTLP Exporter

Update `src/agent.py` to use your OTLP endpoint:

```python
otlp_exporter = OTLPSpanExporter(
    endpoint="https://your-otel-endpoint.com:4317",
    # Add TLS config for production
)
otlp_processor = BatchSpanProcessor(otlp_exporter)
trace.get_tracer_provider().add_span_processor(otlp_processor)
```

### 2. Use OTel Collector

Deploy OTel Collector with the provided config. It will:
- Receive traces via OTLP
- Batch and process them
- Export to your backend (Jaeger, Tempo, etc.)

### 3. Set Up Eval Pipeline

Run eval script periodically:

```bash
# Export traces to JSON (via collector or exporter)
# Then evaluate
python src/eval_from_traces.py traces.json > metrics.json
```

### 4. Add Regression Gates

Compare metrics to baseline:

```python
baseline = load_metrics("baseline.json")
current = load_metrics("current.json")

if current["completion_rate"] < baseline["completion_rate"] * 0.95:
    raise Exception("Completion rate regressed")
```

## Sampling Strategy

The code includes examples of sampling:

- **Keep 100% of failures**: Always sample failed runs
- **Keep long-tail latency**: Sample slow runs (>30s)
- **Sample successes**: 10-20% of successful runs
- **Always keep golden tasks**: Test cases for regression

See the article for full sampling implementation.

## Security

- All span attributes are redacted before export
- PII patterns (emails, SSNs) are automatically redacted
- Secret patterns (API keys, passwords) are redacted
- Large data stored in events, not attributes

## Testing

Test the eval pipeline with the bad run fixture:

```bash
python examples/test_eval.py
```

This demonstrates how the metrics flag a bad run:
- Failed completion
- High tool error count
- Repeated tool calls
- Looping tools

## Next Steps

1. **Instrument your agent**: Add spans around LLM and tool calls
2. **Export traces**: Configure OTLP exporter or use OTel Collector
3. **Build eval pipeline**: Use `eval_from_traces.py` as a starting point
4. **Track metrics**: Set up dashboards for completion rate, cost, tool success
5. **Add regression gates**: Compare metrics in CI/CD

## License

This code is provided as example code for educational purposes.

## References

- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
- [OTel Collector](https://opentelemetry.io/docs/collector/)
- [OTLP Protocol](https://opentelemetry.io/docs/specs/otlp/)
