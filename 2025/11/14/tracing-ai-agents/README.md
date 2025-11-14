# Tracing AI Agents: Logging, Replay, and Debugging

A Python library for tracing AI agent workflows. This library provides logging, replay, and debugging capabilities for tool-using AI agents.

## Features

- **Agent Run Tracing**: Log complete agent runs with steps, tool calls, and outputs
- **Multiple Backends**: In-memory, file-based, or custom backends
- **Replay Capabilities**: Replay past runs to debug issues
- **Metrics Aggregation**: Calculate success rates, tool usage, and error statistics
- **Simple API**: Easy to integrate into existing agent code

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

### Basic Tracing

```python
from src.tracer import Tracer, InMemoryBackend

# Create tracer
tracer = Tracer(backend=InMemoryBackend())

# Start a run
run_id = tracer.start_run({
    "user_input": "What is the weather?",
    "model": "gpt-4"
})

# Log steps
tracer.log_step(run_id, {
    "step_id": 1,
    "tool_name": "search",
    "tool_input": {"query": "weather"},
    "tool_output": {"result": "sunny"}
})

# End run
tracer.end_run(run_id, "It's sunny today")
```

### File-Based Tracing

```python
from src.tracer import Tracer, FileBackend

# Create tracer with file backend
tracer = Tracer(backend=FileBackend("traces.json"))

# Use as normal
run_id = tracer.start_run({"user_input": "Hello"})
# ... log steps ...
tracer.end_run(run_id, "Response")
```

### Instrumented Agent Loop

See `examples/instrumented_agent.py` for a complete example of instrumenting an agent loop.

```python
from examples.instrumented_agent import run_agent_with_tracing
from src.tracer import Tracer, FileBackend

tracer = Tracer(backend=FileBackend("traces.json"))
tools = [
    {"name": "search", "description": "Search for information"},
    {"name": "format", "description": "Format data"}
]

result = run_agent_with_tracing(
    "What is the weather?",
    tools,
    tracer
)
```

### Replaying Traces

```bash
# Replay the most recent trace
python examples/replay.py traces.json

# Replay a specific trace
python examples/replay.py traces.json run_1234567890

# List all traces
python examples/replay.py traces.json --list

# Dry run (show steps without details)
python examples/replay.py traces.json --dry-run
```

### Calculating Metrics

```bash
# Calculate metrics from traces
python examples/metrics.py traces.json

# Include time series data
python examples/metrics.py traces.json --time-series
```

## Architecture

### Components

1. **AgentRun** (`src/agent_run.py`): Data structures for representing agent runs
2. **Tracer** (`src/tracer.py`): Main tracing API with pluggable backends
3. **Backends**: InMemoryBackend, FileBackend, or custom implementations

### Data Structure

An agent run contains:

- **Metadata**: Run ID, user ID, model, config, timestamps
- **Steps**: List of steps, each with tool name, input, output, and messages
- **Final Output**: The final response from the agent
- **Status**: running, success, error, timeout

## Usage Examples

### Example 1: Basic Tracing

```python
from src.tracer import Tracer, InMemoryBackend

tracer = Tracer(backend=InMemoryBackend())
run_id = tracer.start_run({"user_input": "Hello"})

tracer.log_step(run_id, {
    "step_id": 1,
    "tool_name": "greet",
    "tool_input": {"name": "user"},
    "tool_output": {"greeting": "Hello, user!"}
})

tracer.end_run(run_id, "Hello, user!")
```

### Example 2: Error Handling

```python
try:
    run_id = tracer.start_run({"user_input": "Test"})
    # ... agent logic ...
    tracer.end_run(run_id, "Success")
except Exception as e:
    tracer.log_error(run_id, str(e))
```

### Example 3: Custom Backend

```python
from src.tracer import Tracer, TracerBackend
from src.agent_run import AgentRun, AgentStep

class DatabaseBackend:
    def start_run(self, run: AgentRun) -> None:
        # Save to database
        pass
    
    def log_step(self, run_id: str, step: AgentStep) -> None:
        # Save step to database
        pass
    
    # ... implement other methods ...

tracer = Tracer(backend=DatabaseBackend())
```

## Testing

Run the test suite:

```bash
pytest
```

Run with coverage:

```bash
pytest --cov=src --cov-report=html
```

## Best Practices

1. **Start Simple**: Use InMemoryBackend for testing, FileBackend for development
2. **Log Everything**: Log all steps, even if they seem unimportant
3. **Handle Errors**: Always log errors, even if you re-raise them
4. **Keep Traces**: Store traces for at least 30 days for debugging
5. **Privacy**: Hash user IDs, mask PII in tool inputs/outputs
6. **Sampling**: In production, consider sampling (100% errors, 10-20% success)

## Design Principles

This library follows these principles:

1. **Simple API**: Easy to integrate, minimal boilerplate
2. **Pluggable Backends**: Use any storage backend you want
3. **Framework Agnostic**: Works with any agent framework
4. **Minimal Dependencies**: Only standard library + typing
5. **Observability Focus**: Built for debugging and analysis

## Limitations

- Simple file-based storage (extend for production needs)
- Basic error categorization (customize for your use case)
- No built-in PII detection (add your own)
- No distributed tracing (single-process only)

## Contributing

When adding features:

1. Add tests for new functionality
2. Update documentation
3. Consider backward compatibility
4. Test with various agent patterns

## License

This code is provided as example code for educational purposes. Adapt it to your specific requirements and use cases.

