# Project Structure

This document explains the organization of the deterministic AI workflows code examples.

## Directory Layout

```
deterministic-ai-structured-generation/
├── README.md                          # Main documentation
├── STRUCTURE.md                       # This file
├── requirements.txt                   # Python dependencies
├── .env.example                       # Environment template
├── .gitignore                         # Git ignore rules
│
├── src/                               # Source code examples
│   ├── __init__.py
│   ├── 01_schema_definitions.py       # Pydantic schema examples
│   ├── 02_json_schema_generation.py   # Convert schemas for LLMs
│   ├── 03_validation_middleware.py    # Parse and validate outputs
│   ├── 04_retry_logic.py              # Repair loops and retries
│   ├── 05_fastapi_integration.py      # REST API endpoint
│   ├── 08_schema_evolution.py         # Version management
│   ├── 09_observability_metrics.py    # Metrics tracking
│   ├── 10_complete_pipeline.py        # End-to-end example
│   ├── schema_definitions.py          # Shared schemas
│   ├── validation_middleware.py       # Shared validation
│   ├── retry_logic.py                 # Shared retry logic
│   └── observability_metrics.py       # Shared metrics
│
├── tests/                             # Test suite
│   ├── __init__.py
│   └── test_validation.py             # Validation tests
│
└── examples/                          # Sample data
    └── sample_inputs.json             # Test cases
```

## Key Components

### 1. Schema Definitions (`src/01_schema_definitions.py`)

Demonstrates comprehensive Pydantic schema design:
- Required and optional fields
- Enums and literals for controlled values
- Field constraints (min/max, patterns)
- Nested object validation
- Schema versioning

**Run:** `python src/01_schema_definitions.py`

### 2. JSON Schema Generation (`src/02_json_schema_generation.py`)

Shows how to convert Pydantic models to JSON Schema format that LLMs can understand:
- Full schema export
- Simplified schemas for token efficiency
- Prompt construction with schemas

**Run:** `python src/02_json_schema_generation.py`

### 3. Validation Middleware (`src/03_validation_middleware.py`)

Reusable validation wrapper that handles common issues:
- Extract JSON from markdown, extra text
- Fix trailing commas
- Detailed error messages
- Complete validation pipeline

**Run:** `python src/03_validation_middleware.py`

### 4. Retry Logic (`src/04_retry_logic.py`)

Intelligent retry strategies:
- Validation-based retry with error feedback
- Exponential backoff
- Repair prompts that show specific errors
- Max retry limits

**Run:** `python src/04_retry_logic.py`

### 5. FastAPI Integration (`src/05_fastapi_integration.py`)

Production-ready REST API:
- `/extract` endpoint with schema validation
- `/health` for monitoring
- `/schema` to view current schema
- Full error handling

**Run:** `uvicorn src.05_fastapi_integration:app --reload`

### 8. Schema Evolution (`src/08_schema_evolution.py`)

Version management and migration:
- Multiple schema versions (V1, V2, V3)
- Migration functions between versions
- Shadow mode testing (run both versions)
- Backward compatibility checks

**Run:** `python src/08_schema_evolution.py`

### 9. Observability Metrics (`src/09_observability_metrics.py`)

Comprehensive metrics tracking:
- Validation success rate
- Retry rate
- Parse failure rate
- Latency percentiles (P50, P95, P99)
- Field population rates
- Error frequency
- Prometheus export format

**Run:** `python src/09_observability_metrics.py`

### 10. Complete Pipeline (`src/10_complete_pipeline.py`)

End-to-end example combining all components:
- Prompt construction
- LLM calls (mocked)
- Parsing and validation
- Retry with repair
- Metrics collection
- Error handling
- Complete metadata

**Run:** `python src/10_complete_pipeline.py`

## Shared Modules

These modules are imported by the numbered examples:

- **`schema_definitions.py`**: Common schemas (TaskV1, TaskV2)
- **`validation_middleware.py`**: JSON parsing and validation
- **`retry_logic.py`**: Retry strategies and repair prompts
- **`observability_metrics.py`**: Metrics collection

## Testing

Run tests with pytest:

```bash
# All tests
pytest

# Specific test file
pytest tests/test_validation.py

# With coverage
pytest --cov=src tests/

# Verbose output
pytest -v
```

Tests include:
- Unit tests for validation logic
- Property-based tests with Hypothesis
- Golden test cases
- Edge case handling

## Sample Data

`examples/sample_inputs.json` contains:
- 10 test cases for task extraction
- Expected outputs for validation
- Various priority levels and categories

## Configuration

`.env.example` shows required environment variables:
- `OPENAI_API_KEY`: Your OpenAI API key
- `OPENAI_BASE_URL`: API endpoint (optional)
- `MODEL_NAME`: Model to use (optional)

Copy to `.env` and fill in your values:

```bash
cp .env.example .env
```

## Running Examples

All numbered examples are standalone and can be run directly:

```bash
python src/01_schema_definitions.py
python src/02_json_schema_generation.py
python src/03_validation_middleware.py
# ... etc
```

The FastAPI example requires starting the server:

```bash
uvicorn src.05_fastapi_integration:app --reload
```

Then visit `http://localhost:8000/docs` for interactive documentation.

## Dependencies

See `requirements.txt` for all dependencies:
- `pydantic>=2.5.0` - Schema definition and validation
- `openai>=1.10.0` - LLM API client
- `fastapi>=0.109.0` - REST API framework
- `uvicorn>=0.27.0` - ASGI server
- `pytest>=7.4.0` - Testing framework
- `hypothesis>=6.98.0` - Property-based testing

Install with:

```bash
pip install -r requirements.txt
```

## Design Principles

This codebase demonstrates:

1. **Schema-First Design**: Define schemas before prompts
2. **Explicit Validation**: Never trust LLM outputs
3. **Graceful Failure**: Retry with feedback, fail safely
4. **Observability**: Track everything for debugging
5. **Composability**: Small, focused modules
6. **Production-Ready**: Error handling, metrics, versioning

## Related

- [Article](https://appropri8.com/blog/2026/07/14/deterministic-ai-structured-generation/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [OpenAI Structured Outputs](https://platform.openai.com/docs/guides/structured-outputs)
