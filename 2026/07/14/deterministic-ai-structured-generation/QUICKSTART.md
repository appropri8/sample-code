# Quick Start Guide

Get up and running with the deterministic AI workflows examples in 5 minutes.

## Prerequisites

- Python 3.10 or higher
- pip (Python package installer)
- (Optional) OpenAI API key for real LLM calls

## Installation

1. **Clone or navigate to this directory**

```bash
cd deterministic-ai-structured-generation
```

2. **Create a virtual environment** (recommended)

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Set up environment** (optional, for real LLM calls)

```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

## Run Your First Example

### 1. Schema Definitions

See comprehensive Pydantic schema examples:

```bash
python3 src/01_schema_definitions.py
```

**Output:** Shows various schema types with validation rules, nested objects, and versioning.

### 2. Validation Middleware

Test JSON parsing and validation:

```bash
python3 src/03_validation_middleware.py
```

**Output:** Demonstrates handling markdown, trailing commas, and validation errors.

### 3. Complete Pipeline

Run the full end-to-end workflow:

```bash
python3 src/10_complete_pipeline.py
```

**Output:** 
- 10 extraction attempts with varying inputs
- Metrics summary with success rates
- Latency percentiles
- Alert checking

### 4. FastAPI Server

Start the REST API:

```bash
uvicorn src.05_fastapi_integration:app --reload
```

Then open your browser to http://localhost:8000/docs for interactive API documentation.

Test the API:

```bash
curl -X POST http://localhost:8000/extract \
  -H "Content-Type: application/json" \
  -d '{"text": "High priority: Fix critical login bug in auth service"}'
```

## Run Tests

Execute the test suite:

```bash
# All tests
pytest

# With verbose output
pytest -v

# With coverage report
pytest --cov=src tests/
```

## What Each Example Shows

| Example | Key Concepts | Run Time |
|---------|--------------|----------|
| 01 - Schemas | Required/optional fields, enums, constraints | < 1s |
| 02 - JSON Schema | Converting Pydantic to JSON Schema | < 1s |
| 03 - Validation | Parsing, validation, error handling | < 1s |
| 04 - Retry Logic | Repair loops, exponential backoff | 2-3s |
| 05 - FastAPI | REST API, production patterns | Server |
| 08 - Evolution | Versioning, migrations, shadow mode | < 1s |
| 09 - Metrics | Success rates, latency, alerting | < 1s |
| 10 - Complete | Full pipeline with all features | 2-3s |

## Common Issues

### ModuleNotFoundError

**Problem:** `ModuleNotFoundError: No module named 'pydantic'`

**Solution:** Install dependencies:
```bash
pip install -r requirements.txt
```

### ImportError in Examples

**Problem:** Examples can't import from `src` modules

**Solution:** Run from the project root:
```bash
python3 src/01_schema_definitions.py
```

### FastAPI Not Starting

**Problem:** `ModuleNotFoundError: No module named 'fastapi'`

**Solution:** 
```bash
pip install fastapi uvicorn
```

## Next Steps

1. **Read the main README.md** for detailed documentation
2. **Check STRUCTURE.md** to understand the codebase organization
3. **Modify the examples** - Change schemas, add fields, test edge cases
4. **Run with real LLMs** - Set up `.env` and replace mock calls with real API calls
5. **Integrate into your project** - Copy patterns you need

## Quick Reference

### Running Examples

```bash
# Schema definitions
python3 src/01_schema_definitions.py

# Validation
python3 src/03_validation_middleware.py

# Retry logic
python3 src/04_retry_logic.py

# Complete pipeline
python3 src/10_complete_pipeline.py

# All numbered examples
for f in src/0*.py src/10*.py; do python3 "$f"; done
```

### Testing

```bash
# Run all tests
pytest

# Run specific test
pytest tests/test_validation.py

# Watch mode (requires pytest-watch)
ptw
```

### Development

```bash
# Install in editable mode
pip install -e .

# Format code (if you have black installed)
black src/ tests/

# Type checking (if you have mypy installed)
mypy src/
```

## Learn More

- [Main README](README.md) - Full documentation
- [Structure Guide](STRUCTURE.md) - Codebase organization
- [Article](https://appropri8.com/blog/2026/07/14/deterministic-ai-structured-generation/) - Original blog post
- [Pydantic Docs](https://docs.pydantic.dev/) - Schema validation library
- [OpenAI Structured Outputs](https://platform.openai.com/docs/guides/structured-outputs) - Native LLM support

## Need Help?

Check the [main README.md](README.md) for:
- Detailed API documentation
- Common patterns and best practices
- Troubleshooting guide
- Performance tips
- Production deployment checklist
