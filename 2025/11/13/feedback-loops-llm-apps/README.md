# Feedback Loops for LLM Apps in Production

A Python library for building practical feedback loops in LLM applications. This library provides logging, feedback collection, metrics calculation, A/B testing, and offline evaluation capabilities.

## Features

- **Request Logging**: Log all LLM interactions with sanitization and PII removal
- **Feedback Collection**: Capture explicit, implicit, and outcome-based feedback
- **Metrics Calculation**: Compute quality, safety, and cost metrics
- **A/B Testing**: Route traffic between prompt versions and compare results
- **Shadow Runs**: Test new versions safely without exposing to users
- **Offline Evaluation**: Use LLM judges to evaluate prompt versions
- **Feedback Database**: PostgreSQL schema for storing feedback data

## Installation

```bash
pip install -r requirements.txt
```

Set your OpenAI API key:

```bash
export OPENAI_API_KEY="your-api-key-here"
```

Set up PostgreSQL database:

```bash
# Create database
createdb feedback_loops

# Run schema
psql feedback_loops < src/schema.sql
```

## Quick Start

### Basic Logging

```python
from src.logging_middleware import log_llm_request
from fastapi import FastAPI

app = FastAPI()

@app.post("/api/llm")
async def llm_endpoint(request: dict):
    # Your LLM call here
    result = call_llm(request["input"])
    
    # Logging is handled by middleware
    return result
```

### Collecting Feedback

```python
from src.feedback import insert_feedback, collect_explicit_feedback

# Explicit feedback
collect_explicit_feedback(
    request_id="req_123",
    rating=5,
    comment="Great answer!"
)

# Outcome-based feedback
insert_feedback(
    conversation_id="conv_456",
    turn_id=1,
    request_id="req_123",
    input_text="How do I handle errors?",
    output_text="Use try-except blocks...",
    prompt_version="v1",
    model="gpt-4",
    feedback_type="outcome",
    feedback_value={"task_succeeded": True}
)
```

### Calculating Metrics

```python
from src.metrics import compare_prompt_versions, calculate_task_success_rate
from src.database import get_feedback_data

# Get feedback data
feedback_data = get_feedback_data()

# Compare prompt versions
comparison = compare_prompt_versions(feedback_data)

for version, metrics in comparison.items():
    print(f"{version}: {metrics['task_success_rate']:.2%} success rate")
```

### A/B Testing

```python
from src.ab_testing import route_to_variant, log_ab_test

# Route user to variant
variants = {"v1": 0.8, "v2": 0.2}
variant = route_to_variant(user_id, variants)

# Use variant
prompt = get_prompt(variant)
result = call_llm(input_text, prompt)

# Log A/B test
log_ab_test(request_id, user_id, variant, result)
```

### Offline Evaluation

```python
from src.evaluation import evaluate_prompt_version, compare_prompt_versions

# Load logged interactions
interactions = load_logged_interactions()

# Evaluate versions
comparison = compare_prompt_versions(interactions)

for version, metrics in comparison.items():
    print(f"{version}:")
    print(f"  Avg clarity: {metrics['avg_clarity']:.2f}")
    print(f"  Avg usefulness: {metrics['avg_usefulness']:.2f}")
```

## Architecture

### Components

1. **Logging Middleware** (`src/logging_middleware.py`): FastAPI middleware for logging requests
2. **Feedback Collection** (`src/feedback.py`): Functions for collecting and storing feedback
3. **Database Schema** (`src/schema.sql`): PostgreSQL schema for feedback table
4. **Metrics** (`src/metrics.py`): Calculate quality, safety, and cost metrics
5. **A/B Testing** (`src/ab_testing.py`): Route traffic and compare variants
6. **Shadow Runs** (`src/shadow_runs.py`): Run new versions in background
7. **Evaluation** (`src/evaluation.py`): Offline evaluation with LLM judges

## Usage Examples

### Example 1: Basic Logging

See `examples/basic_logging.py` for a complete FastAPI example with logging middleware.

### Example 2: Feedback Collection

See `examples/feedback_collection.py` for examples of collecting different types of feedback.

### Example 3: A/B Testing

See `examples/ab_testing.py` for a complete A/B testing setup.

### Example 4: Offline Evaluation

See `examples/offline_evaluation.py` for evaluating prompts offline.

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

1. **Logging**: Always sanitize inputs and hash user IDs
2. **Sampling**: Don't log everything - sample intelligently
3. **Privacy**: Remove PII, set retention policies
4. **Metrics**: Focus on 2-3 metrics that matter
5. **Experiments**: Start with shadow runs, then A/B tests
6. **Approval**: Require human approval before promoting prompts

## Design Principles

This library implements best practices for feedback loops:

1. **Comprehensive Logging**: Log inputs, outputs, metadata, and outcomes
2. **Structured Feedback**: Store feedback in a queryable database
3. **Meaningful Metrics**: Calculate metrics that connect to goals
4. **Safe Experimentation**: A/B tests and shadow runs reduce risk
5. **Automated Evaluation**: Use LLM judges to reduce labeling burden

## Limitations

- Simple PostgreSQL schema (extend for production needs)
- Basic PII sanitization (use proper tools in production)
- Token counting is approximate
- Cost estimates based on published pricing

## Contributing

When adding features:
1. Add tests for new functionality
2. Update documentation
3. Consider privacy and security implications
4. Test with various feedback types

## License

This code is provided as example code for educational purposes. Adapt it to your specific requirements and use cases.

