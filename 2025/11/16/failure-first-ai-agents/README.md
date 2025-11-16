# Failure-First AI Agents: Designing Timeouts, Fallbacks, and Human Handoffs

A Python library demonstrating how to build AI agents that handle failures gracefully. This implementation shows how to design agents that fail safely instead of failing loudly.

## Features

- **Retry with Backoff**: Smart retry logic with exponential backoff
- **Timeouts**: Per-tool and per-workflow timeouts
- **Fallback Chains**: Graceful degradation when tools fail
- **Human Handoffs**: Approval gateways and escalation patterns
- **Observability**: Structured logging and metrics collection
- **Failure Testing**: Utilities for testing failure scenarios

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

### Basic Usage

```python
import asyncio
from src.agent import FailureFirstAgent, ToolConfig
from src.fallback_chain import PrimaryTool, ReadOnlyTool, ToolWithFallback

# Configure tools
tool_configs = {
    "search": ToolConfig(
        name="search",
        timeout=10.0,
        max_retries=3,
        requires_approval=False
    )
}

# Create agent
agent = FailureFirstAgent(
    tool_configs=tool_configs,
    workflow_timeout=300.0,
    escalation_threshold=3
)

# Register tools with fallback
search_primary = PrimaryTool("search_api", simulate_failure=False)
search_readonly = ReadOnlyTool("search_api")
search_tool = ToolWithFallback(
    primary_tool=search_primary,
    fallback_tools=[search_readonly]
)
agent.register_tool("search", search_tool)

# Run workflow
plan = [
    {"tool": "search", "params": {"query": "test"}}
]

result = await agent.run("Search for test", plan)
print(result)
```

### Retry and Timeout

```python
from src.retry_timeout import retry_with_backoff

async def unreliable_api():
    # Your API call here
    pass

# Retry with backoff
result = await retry_with_backoff(
    unreliable_api,
    max_attempts=3,
    base_delay=1.0,
    timeout=5.0
)
```

### Fallback Chain

```python
from src.fallback_chain import (
    PrimaryTool,
    CachedTool,
    ReadOnlyTool,
    ToolWithFallback
)

# Create tools
primary = PrimaryTool("api", simulate_failure=False)
cached = CachedTool("api", cache={"key": "value"})
readonly = ReadOnlyTool("api")

# Create tool with fallback
tool = ToolWithFallback(
    primary_tool=primary,
    fallback_tools=[cached, readonly]
)

# Call tool (automatically falls back if primary fails)
result = await tool.call({"param": "value"})
```

### Human Handoff

```python
from src.human_handoff import HumanHandoff, HandoffContext

handoff = HumanHandoff()

# Request approval
action = {"type": "payment", "amount": 100.0}
context = HandoffContext(
    user_input="Process payment",
    plan={},
    executed_steps=[],
    failing_step=None,
    error=None
)

result = await handoff.ask_before_act(action, context)
```

## Examples

### Example 1: Basic Usage

```bash
python examples/basic_usage.py
```

Shows how to:
- Create an agent with tool configurations
- Register tools with fallback chains
- Run a workflow with failure handling

### Example 2: Retry and Timeout

```bash
python examples/retry_timeout_example.py
```

Demonstrates:
- Retry logic with exponential backoff
- Timeout handling
- Decorator pattern for automatic retry/timeout

### Example 3: Fallback Chain

```bash
python examples/fallback_example.py
```

Shows:
- Primary tool success
- Fallback to cache
- Fallback to read-only
- Handling all failures

### Example 4: Human Handoff

```bash
python examples/handoff_example.py
```

Demonstrates:
- Approval gateway
- Escalation manager
- Stop and escalate pattern
- Context packaging

## Architecture

### Components

1. **Retry and Timeout** (`src/retry_timeout.py`): Retry logic with backoff and timeouts
2. **Fallback Chain** (`src/fallback_chain.py`): Tool fallback patterns
3. **Human Handoff** (`src/human_handoff.py`): Approval and escalation patterns
4. **Agent** (`src/agent.py`): Main agent implementation with failure handling
5. **Observability** (`src/observability.py`): Logging and metrics

## Design Principles

### 1. Fail Safely

Every tool call can fail. Every model call can fail. Plan for it.

### 2. Smart Retries

Retry server errors. Don't retry client errors. Use exponential backoff.

### 3. Graceful Degradation

When something fails, fall back to something simpler. Make it explicit.

### 4. Human in the Loop

Some actions need approval. Some errors need escalation. Know when to stop.

### 5. Observability

Log everything. Track errors. Alert on spikes. Make failures visible.

## Testing

Run the test suite:

```bash
pytest
```

Run with coverage:

```bash
pytest --cov=src --cov-report=html
```

## Failure Testing

Test failure scenarios in staging:

```python
from src.fallback_chain import PrimaryTool

# Simulate failures
primary = PrimaryTool("api", simulate_failure=True)
# Tool will fail, triggering fallback chain
```

## Best Practices

1. **Set Timeouts**: Every tool should have a timeout
2. **Configure Retries**: Set max retries per tool type
3. **Define Fallbacks**: Have a fallback for critical tools
4. **Require Approvals**: High-risk actions need approval
5. **Log Everything**: Structured logs help debug failures
6. **Test Failures**: Test failure scenarios, not just success

## Limitations

- Simple in-memory implementations (extend for distributed systems)
- Simulated tool calls (implement real API calls)
- Basic logging (enhance for production observability)
- Simple approval system (integrate with real approval workflows)

## Extending the Implementation

### Adding Real API Calls

Replace simulated calls with real API clients:

```python
async def _call_tool(self, tool_name: str, params: Dict) -> Any:
    if tool_name == "payment_gateway":
        return await payment_client.charge(params)
    elif tool_name == "search_api":
        return await search_client.search(params)
```

### Adding Distributed Observability

For production, use a real observability stack:

```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

async def call_tool(self, tool_name: str, params: Dict):
    with tracer.start_as_current_span(f"tool.{tool_name}"):
        # Call tool
        pass
```

## Contributing

When adding features:

1. Add tests for new functionality
2. Update documentation
3. Follow existing code patterns
4. Ensure failure handling is comprehensive

## License

This code is provided as example code for educational purposes. Adapt it to your specific requirements and use cases.

