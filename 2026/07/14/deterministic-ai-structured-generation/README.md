# Deterministic AI Workflows - Code Examples

This repository contains working code examples for the article "Designing Deterministic AI Workflows with Structured Generation and Schema-Constrained Outputs".

## Overview

These examples demonstrate practical patterns for building reliable AI systems using:

1. **Pydantic Schema Definitions** - Type-safe schemas with validation rules
2. **JSON Schema Generation** - Converting Pydantic to LLM-consumable schemas
3. **Validation Middleware** - Reusable validation with detailed error reporting
4. **Retry Logic** - Repair loops with exponential backoff
5. **FastAPI Integration** - Production-ready REST endpoints
6. **Typed Response Handlers** - Type-safe response processing
7. **Unit Tests** - Property-based and golden test cases
8. **Schema Evolution** - Versioning and migration strategies
9. **Observability Metrics** - Prometheus-style metrics
10. **Complete Pipeline** - End-to-end working example

## Setup

### Requirements

- Python 3.10+
- OpenAI API key (or compatible endpoint)

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Add your API key to .env
# OPENAI_API_KEY=your_key_here
```

### Environment Variables

Create a `.env` file:

```env
OPENAI_API_KEY=your_openai_key_here
OPENAI_BASE_URL=https://api.openai.com/v1  # Optional, defaults to OpenAI
MODEL_NAME=gpt-4-turbo-preview  # Or gpt-3.5-turbo, etc.
```

## Examples

### 1. Schema Definitions

```bash
python src/01_schema_definitions.py
```

Shows how to define Pydantic schemas with:
- Required and optional fields
- Enums and literals
- Field constraints (min, max, pattern)
- Nested objects
- Versioning

### 2. JSON Schema Generation

```bash
python src/02_json_schema_generation.py
```

Demonstrates converting Pydantic models to JSON Schema for LLM consumption.

### 3. Validation Middleware

```bash
python src/03_validation_middleware.py
```

Reusable validation wrapper that:
- Parses JSON from model output
- Validates against schema
- Returns detailed error messages
- Handles common edge cases

### 4. Retry Logic

```bash
python src/04_retry_logic.py
```

Shows repair loop patterns:
- Validation-based retry
- Repair prompts with error feedback
- Exponential backoff
- Max retry limits

### 5. FastAPI Integration

```bash
# Start the server
uvicorn src.05_fastapi_integration:app --reload

# In another terminal, test it
curl -X POST http://localhost:8000/extract \
  -H "Content-Type: application/json" \
  -d '{"text": "High priority: Fix login bug in auth service"}'
```

Production-ready REST endpoint with schema validation.

### 6. Typed Response Handler

```bash
python src/06_typed_response_handler.py
```

Type-safe response processing with exhaustive error handling.

### 7. Unit Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_validation.py

# Run with coverage
pytest --cov=src tests/
```

Includes:
- Property-based tests with Hypothesis
- Golden test cases
- Schema validation tests
- Retry logic tests

### 8. Schema Evolution

```bash
python src/08_schema_evolution.py
```

Demonstrates:
- Schema versioning
- Backward compatibility
- Migration strategies
- Shadow mode testing

### 9. Observability Metrics

```bash
python src/09_observability_metrics.py
```

Tracks and exports:
- Validation success rate
- Retry rate
- Parse failure rate
- Latency percentiles
- Schema drift

### 10. Complete Pipeline

```bash
python src/10_complete_pipeline.py
```

End-to-end example tying everything together:
- Prompt construction
- LLM generation
- Parsing
- Validation
- Retry with repair
- Metrics collection
- Error handling

## Project Structure

```
deterministic-ai-structured-generation/
├── README.md
├── requirements.txt
├── .gitignore
├── .env.example
├── src/
│   ├── __init__.py
│   ├── 01_schema_definitions.py
│   ├── 02_json_schema_generation.py
│   ├── 03_validation_middleware.py
│   ├── 04_retry_logic.py
│   ├── 05_fastapi_integration.py
│   ├── 06_typed_response_handler.py
│   ├── 08_schema_evolution.py
│   ├── 09_observability_metrics.py
│   ├── 10_complete_pipeline.py
│   └── utils/
│       ├── __init__.py
│       ├── llm_client.py
│       └── parsers.py
├── tests/
│   ├── __init__.py
│   ├── test_validation.py
│   ├── test_retry.py
│   └── test_schemas.py
└── examples/
    └── sample_inputs.json
```

## Key Concepts

### Schema-First Design

Start with the schema. Define what your system needs. Make it explicit.

```python
class TaskExtraction(BaseModel):
    title: str = Field(min_length=5, max_length=100)
    priority: Literal[1, 2, 3, 4, 5]
    category: Literal["bug", "feature", "docs", "refactor"]
```

### Validation Pipeline

```
Input → Prompt → LLM → Parse → Validate → Retry → Output
```

Each step has one job. Failures are explicit.

### Repair Loops

Don't retry blindly. Show the model what broke:

```python
Your previous output had these errors:
- priority: must be 1-5
- email: invalid format

Fix ONLY these fields.
```

### Metrics That Matter

- **Validation success rate**: Target 80%+
- **Retry rate**: Target <20%
- **Parse failures**: Target <5%
- **Latency P95**: Know your SLO

## Common Patterns

### 1. Required vs Optional Fields

```python
# Required: System breaks without these
title: str
priority: Literal[1, 2, 3, 4, 5]

# Optional: Nice to have
description: str | None = None
tags: list[str] = Field(default_factory=list)
```

### 2. Enum Constraints

```python
# Bad: Unbounded string
status: str

# Good: Fixed set
status: Literal["open", "in_progress", "done"]
```

### 3. Number Ranges

```python
# Enforce valid ranges
priority: int = Field(ge=1, le=5)
confidence: float = Field(ge=0.0, le=1.0)
estimated_hours: float = Field(ge=0.5, le=80.0)
```

### 4. Nested Validation

```python
class Address(BaseModel):
    street: str
    city: str
    country: str = Field(pattern="^[A-Z]{2}$")

class Customer(BaseModel):
    name: str
    address: Address  # Validates nested object
```

### 5. Schema Versioning

```python
class TaskV1(BaseModel):
    version: Literal["1.0"] = "1.0"
    title: str

class TaskV2(BaseModel):
    version: Literal["2.0"] = "2.0"
    title: str
    priority: Literal[1, 2, 3, 4, 5]  # New required field
```

## Testing Strategy

### Golden Test Cases

Test with known valid/invalid inputs:

```python
VALID_CASES = [
    {"title": "Fix bug", "priority": 3, "category": "bug"},
    {"title": "Add feature", "priority": 5, "category": "feature"},
]

INVALID_CASES = [
    {"title": "x", "priority": 3},  # Title too short
    {"title": "Fix bug", "priority": 6},  # Priority out of range
]
```

### Property-Based Testing

Generate random valid inputs:

```python
@given(
    title=st.text(min_size=5, max_size=100),
    priority=st.integers(min_value=1, max_value=5)
)
def test_task_extraction(title, priority):
    task = TaskExtraction(title=title, priority=priority)
    assert task.title == title
    assert task.priority == priority
```

### Regression Tests

Test schema migrations don't break existing data.

## Performance Tips

1. **Keep schemas small** - One task per schema
2. **Use enums** - Reduce infinite possibilities to fixed sets
3. **Limit retries** - Max 2-3 attempts
4. **Cache prompts** - Reuse stable system prompts
5. **Log everything** - Debug production issues easily

## Monitoring in Production

### Alerts to Set Up

```python
# Validation failure rate > 30%
if validation_success_rate < 0.7:
    alert("High validation failure rate")

# Retry rate > 30%
if retry_rate > 0.3:
    alert("High retry rate")

# P95 latency > 5s
if p95_latency > 5.0:
    alert("High latency")
```

### Logs to Keep

- Prompt hash
- Response hash
- Validation success/failure
- Retry count
- Latency
- Schema version
- Timestamp

## Troubleshooting

### High Validation Failure Rate

- Check if schema is too strict
- Review prompt clarity
- Check if model understands field descriptions
- Look at common error patterns

### High Retry Rate

- Simplify schema
- Improve prompt instructions
- Check if repair prompts are clear
- Consider fallback model

### Parse Failures

- Check for markdown in responses
- Look for extra text around JSON
- Verify JSON structure in prompts
- Test with different models

## License

MIT

## Related

- [Article](https://appropri8.com/blog/2026/07/14/deterministic-ai-structured-generation/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [OpenAI Structured Outputs](https://platform.openai.com/docs/guides/structured-outputs)
- [Instructor Library](https://github.com/jxnl/instructor)
