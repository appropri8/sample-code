# LLM Observability & MLOps

A Python library for instrumenting LLM workflows with comprehensive observability. Track prompts, tokens, costs, branching decisions, tool calls, and detect anomalies in production.

## Features

- **LLM Call Logging**: Automatic logging of all LLM API calls with tokens, latency, and cost tracking
- **Workflow Observability**: Track branching decisions and tool invocations
- **Prometheus Metrics**: Export metrics for dashboards and alerting
- **Anomaly Detection**: Detect token spikes, cost increases, latency issues, and branch rate changes
- **Dashboard**: Streamlit dashboard for visualizing metrics
- **SQLite Storage**: Lightweight database for storing logs and metrics

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

### Basic Example

```python
from src import ObservabilityLogger, InstrumentedLLM

# Initialize logger
logger = ObservabilityLogger()

# Create instrumented LLM
llm = InstrumentedLLM(logger)

# Make a call (automatically logged)
result = llm.call(
    prompt="What is the capital of France?",
    model="gpt-3.5-turbo",
    prompt_version="v1"
)

print(result["content"])
```

### Workflow Example

```python
from examples.basic_workflow import ObservabilityWorkflow

workflow = ObservabilityWorkflow()
result = workflow.process_request("How do I reset my password?")
print(result)
```

### Run Examples

```bash
# Basic workflow
python examples/basic_workflow.py

# Advanced multi-step workflow
python examples/advanced_workflow.py
```

### View Dashboard

```bash
streamlit run dashboard.py
```

### Check for Anomalies

```bash
python anomaly_detector.py
```

## Architecture

### Components

**ObservabilityLogger**: Logs LLM calls to SQLite and exports to Prometheus
- Tracks tokens, latency, cost per call
- Stores full prompts and responses
- Exports metrics for monitoring

**InstrumentedLLM**: Wrapper around OpenAI client with automatic logging
- Transparent API (same as OpenAI client)
- Automatic request ID generation
- Error handling and logging

**WorkflowLogger**: Logs workflow-specific events
- Branching decisions
- Tool invocations
- Execution paths

**AnomalyDetector**: Detects unusual patterns
- Token usage spikes
- Cost increases
- Latency degradation
- Branch rate changes

### Database Schema

**llm_calls**: Stores all LLM API calls
- timestamp, request_id, prompt_version, model
- prompt, response, tokens, latency, cost
- status, error, metadata

**branch_decisions**: Stores branching logic
- timestamp, request_id, from_node, to_node
- condition, condition_result, context

**tool_calls**: Stores tool invocations
- timestamp, request_id, tool_name
- inputs, output, latency, status, error

## Usage

### Logging LLM Calls

```python
from src import ObservabilityLogger, InstrumentedLLM

logger = ObservabilityLogger(db_path="my_observability.db")
llm = InstrumentedLLM(logger)

result = llm.call(
    prompt="Your prompt here",
    model="gpt-4",
    prompt_version="v2"
)
```

### Logging Branch Decisions

```python
from src import WorkflowLogger

workflow_logger = WorkflowLogger()

workflow_logger.log_branch_decision(
    request_id="req-123",
    from_node="generate_response",
    to_node="human_review",
    condition="confidence < 0.7",
    condition_result=True,
    context={"confidence": 0.6}
)
```

### Logging Tool Calls

```python
import time

start_time = time.time()
result = my_tool(input_data)
latency_ms = (time.time() - start_time) * 1000

workflow_logger.log_tool_call(
    request_id="req-123",
    tool_name="external_api",
    inputs={"data": input_data},
    output=result,
    latency_ms=latency_ms,
    status="success"
)
```

### Anomaly Detection

```python
from src import AnomalyDetector

detector = AnomalyDetector()
anomalies = detector.check_anomalies()

if anomalies:
    detector.alert(anomalies)
```

## Prometheus Integration

Metrics are automatically exported. Start Prometheus server:

```bash
# Install Prometheus (if not installed)
# Then configure prometheus.yml to scrape metrics

# In your code, expose metrics endpoint
from prometheus_client import start_http_server

start_http_server(8000)  # Metrics available at http://localhost:8000/metrics
```

## Dashboard

The Streamlit dashboard shows:
- Cost trends over time
- Token usage by prompt version
- Latency metrics
- Branch distribution
- Key metrics summary

Run with:
```bash
streamlit run dashboard.py
```

## Testing

```bash
pytest
```

## Project Structure

```
observability-mlops-llms/
├── src/
│   ├── __init__.py
│   ├── logger.py              # LLM call logging
│   ├── llm_wrapper.py          # Instrumented LLM wrapper
│   ├── workflow_logger.py      # Workflow and branch logging
│   └── anomaly_detector.py     # Anomaly detection
├── examples/
│   ├── basic_workflow.py       # Simple workflow example
│   └── advanced_workflow.py    # Multi-step workflow
├── tests/
│   ├── test_logger.py
│   └── test_anomaly_detector.py
├── dashboard.py                 # Streamlit dashboard
├── anomaly_detector.py          # Standalone anomaly checker
├── requirements.txt
├── pytest.ini
└── README.md
```

## Configuration

### Database Path

Default is `observability.db`. Change by passing `db_path` parameter:

```python
logger = ObservabilityLogger(db_path="custom_path.db")
```

### Model Pricing

Update pricing in `logger.py` `_calculate_cost` method for current rates.

### Anomaly Thresholds

Adjust thresholds in `anomaly_detector.py`:
- Token spike: 1.5x increase
- Cost spike: 2x increase
- Latency spike: 1.5x increase
- Branch rate change: 0.2 absolute change

## Extending

### Add Custom Metrics

Extend `ObservabilityLogger` to track additional metrics:

```python
class CustomLogger(ObservabilityLogger):
    def log_llm_call(self, ...):
        # Call parent
        log_entry = super().log_llm_call(...)
        
        # Add custom tracking
        self._track_custom_metric(log_entry)
        
        return log_entry
```

### Custom Anomaly Detection

Extend `AnomalyDetector`:

```python
class CustomAnomalyDetector(AnomalyDetector):
    def check_anomalies(self):
        anomalies = super().check_anomalies()
        
        # Add custom checks
        custom_anomalies = self._check_custom_patterns()
        anomalies.extend(custom_anomalies)
        
        return anomalies
```

## Best Practices

1. **Version your prompts**: Always specify `prompt_version` when calling LLM
2. **Track branches**: Log all branching decisions for debugging
3. **Monitor costs**: Set up alerts for cost spikes
4. **Test anomalies**: Regularly test anomaly detection
5. **Retention policies**: Set up database cleanup for old logs
6. **Privacy**: Sanitize logs before storing (remove PII)

## License

MIT

## Contributing

Contributions welcome! Please open an issue or PR.

