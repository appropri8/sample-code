# Multi-Agent Mesh Observability: Tracing One Task Across 5 Agents with OpenTelemetry

Complete executable code sample demonstrating end-to-end tracing in a multi-agent mesh system using OpenTelemetry.

## Overview

This repository contains a working implementation of a 5-agent system with distributed tracing:

- **Planner Agent**: Receives user request, decides what to do
- **Tool Agent**: Calls external tools with retry logic
- **Verifier Agent**: Validates results
- **Summarizer Agent**: Formats output
- **Mesh Router**: Routes messages between agents, preserves trace context

All agents and tools create OpenTelemetry spans. Trace context is propagated via W3C Trace Context (`traceparent` header) in message envelopes.

## Architecture

```
User Request
    ↓
Planner Agent (creates plan)
    ↓
Tool Agent (calls search tool, with retries)
    ↓
Verifier Agent (validates result)
    ↓
Summarizer Agent (formats output)
    ↓
Response
```

Each step creates a span. Tool calls create nested spans. Retries create child spans. You see one trace with the full story.

## Prerequisites

- Python 3.8+
- Docker and Docker Compose (for Jaeger)
- pip

## Installation

1. Clone this repository

2. Install Python dependencies:

```bash
pip install -r requirements.txt
```

3. Start Jaeger and OpenTelemetry Collector:

```bash
docker-compose up -d
```

Wait for services to be healthy (check with `docker-compose ps`).

## Quick Start

Run the example:

```bash
python examples/run_example.py
```

You should see output like:

```
Setting up OpenTelemetry tracing...
Creating tools...
Creating agents...
Creating mesh router...

Starting workflow...
Trace ID: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01

Result: Result: Search results for: Find information about Python

Check Jaeger UI at http://localhost:16686 to see the trace!
```

## Viewing Traces

1. Open Jaeger UI: http://localhost:16686

2. Select service: `multi-agent-mesh`

3. Click "Find Traces"

You should see a trace with this structure:

```
Trace: trace-abc-123
├── Span: user-request (root)
│   ├── Span: agent.planner-agent.process
│   ├── Span: agent.tool-agent.process
│   │   ├── Span: tool-agent.retry.1 (failed)
│   │   └── Span: tool-agent.retry.2 (success)
│   │       └── Span: tool.search-api.call
│   ├── Span: agent.verifier-agent.process
│   └── Span: agent.summarizer-agent.process
```

## Expected Output

When you view the trace in Jaeger, you should see:

- **One root span** for the user request
- **Child spans** for each agent hop
- **Nested spans** for tool calls
- **Retry spans** showing failed and successful attempts
- **Attributes** on each span:
  - `agent.name`, `agent.role`
  - `tool.name`, `tool.type`
  - `conversation.id`, `workflow.id`
  - `retry.attempt`, `retry.success`
  - `tool.duration_ms`, `tool.success`

## Repository Structure

```
.
├── README.md
├── requirements.txt
├── docker-compose.yml
├── otel-collector-config.yaml
├── src/
│   ├── tracing/
│   │   ├── setup.py              # OpenTelemetry setup
│   │   └── redaction.py          # PII redaction utilities
│   ├── agents/
│   │   ├── base_agent.py         # Base agent with tracing
│   │   ├── planner_agent.py      # Planner agent
│   │   ├── tool_agent.py         # Tool agent with retries
│   │   ├── verifier_agent.py     # Verifier agent
│   │   └── summarizer_agent.py   # Summarizer agent
│   ├── tools/
│   │   ├── base_tool.py          # Base tool with tracing
│   │   └── search_tool.py        # Mock search tool
│   └── mesh/
│       └── router.py             # Mesh router
└── examples/
    └── run_example.py            # Example script
```

## Key Concepts

### 1. Trace Context Propagation

Trace context is propagated via W3C Trace Context (`traceparent` header) in message envelopes:

```python
message = {
    "request": "...",
    "traceparent": "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01",
    "conversation_id": "...",
    "workflow_id": "..."
}
```

Each agent extracts the trace context, creates a child span, and passes it forward.

### 2. Span Structure

- **Root span**: `user-request` (created at entry point)
- **Agent spans**: `agent.{name}.process` (one per agent)
- **Tool spans**: `tool.{name}.call` (one per tool call)
- **Retry spans**: `tool-agent.retry.{attempt}` (one per retry)

### 3. Standard Attributes

All spans include standard attributes:

- `agent.name`, `agent.role`
- `tool.name`, `tool.type`, `tool.target`
- `conversation.id`, `workflow.id`
- `retry.attempt`, `retry.success`
- `tool.duration_ms`, `tool.success`

### 4. Error Handling

Errors are recorded on spans:

```python
span.set_attribute("tool.success", False)
span.set_attribute("tool.error", str(e))
span.record_exception(e)
```

## Running Multiple Times

Run the example multiple times to see different traces:

```bash
for i in {1..5}; do
  echo "Run $i:"
  python examples/run_example.py
  sleep 2
done
```

Each run creates a new trace. You can see retry patterns, different latencies, and error scenarios.

## Customization

### Change Jaeger Host/Port

Set environment variables:

```bash
export JAEGER_AGENT_HOST=localhost
export JAEGER_AGENT_PORT=6831
python examples/run_example.py
```

### Enable Debug Mode

Set `OTEL_DEBUG=true` to see more verbose logging:

```bash
export OTEL_DEBUG=true
python examples/run_example.py
```

### Use OTLP Exporter

To use OTLP instead of Jaeger directly, modify `src/tracing/setup.py`:

```python
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

exporter = OTLPSpanExporter(
    endpoint="http://localhost:4317",
    insecure=True
)
```

## Production Considerations

### Sampling

In production, sample traces to reduce overhead:

```python
from opentelemetry.sdk.trace.sampling import TraceIdRatioBased

sampler = TraceIdRatioBased(0.1)  # Sample 10%
provider = TracerProvider(sampler=sampler)
```

### Redaction

Sensitive data is automatically redacted using `src/tracing/redaction.py`. Customize as needed.

### Backend Choice

- **Jaeger**: Good for development, simple setup
- **Tempo**: Grafana integration, good for scale
- **Datadog/New Relic**: Commercial, includes APM features
- **OTel Collector**: Flexible, can export to multiple backends

## Troubleshooting

### Jaeger not receiving traces

1. Check Jaeger is running: `docker-compose ps`
2. Check Jaeger UI: http://localhost:16686
3. Check logs: `docker-compose logs jaeger`
4. Verify port 6831 is not blocked

### No traces in Jaeger UI

1. Wait a few seconds (spans are batched)
2. Refresh the Jaeger UI
3. Check service name is `multi-agent-mesh`
4. Check OpenTelemetry Collector logs: `docker-compose logs otel-collector`

### Import errors

Make sure you're running from the repository root:

```bash
cd /path/to/repository
python examples/run_example.py
```

## Related Article

This code accompanies the article: "Multi-Agent Mesh Observability: Tracing One Task Across 5 Agents with OpenTelemetry"

## License

MIT

