# Schema-First LLM Apps: Make Tool Calling Reliable

A Python library demonstrating schema-first design for LLM applications with JSON Schema validation, repair loops, and safe tool execution.

## Overview

This library shows how to make structured LLM outputs dependable by:
- Defining strict JSON Schemas
- Validating every response
- Auto-repairing invalid outputs (1-2 retries)
- Failing safely with fallbacks
- Logging everything for improvement

## Features

- **Schema + Validator**: JSON Schema definitions with clear error reporting
- **Repair Loop**: Automatic retry with validation error feedback
- **Tool Execution Wrapper**: Safe dispatcher with argument validation
- **Comprehensive Tests**: Test suite with 8+ test cases
- **Bad Output Fixtures**: Real examples of common failures

## Installation

```bash
pip install -r requirements.txt
```

Set your OpenAI API key (optional, for examples):

```bash
export OPENAI_API_KEY="your-api-key-here"
```

## Quick Start

### Schema + Validator

```python
from src.schemas import CustomerExtraction
from src.validator import validate_output, extract_json

# Parse and validate
response = '{"name": "John Doe", "email": "john@example.com", "priority": 3}'
data = extract_json(response)
model, error = validate_output(data, CustomerExtraction)

if model:
    print(f"Valid: {model.name}, {model.email}")
else:
    print(f"Error: {error}")
```

### Repair Loop

```python
from src.repair_loop import repair_loop
from src.schemas import CustomerExtraction

result = repair_loop(
    "Extract customer info: John Doe, john@example.com, priority 3",
    CustomerExtraction,
    max_retries=2
)

if result:
    print(f"Extracted: {result.name}, {result.email}")
else:
    print("Failed after retries")
```

### Tool Execution Wrapper

```python
from src.tool_wrapper import tool_execution_wrapper, GetUserInfoArgs, get_user_info

result = tool_execution_wrapper(
    "get_user_info",
    {"user_id": "user123"},
    get_user_info,
    GetUserInfoArgs
)

if result["success"]:
    print(result["result"])
else:
    print(f"Error: {result['error']}")
```

## Project Structure

```
.
├── src/
│   ├── schemas.py          # JSON Schema definitions
│   ├── validator.py         # Validation with error reporting
│   ├── repair_loop.py      # Repair loop with retry logic
│   └── tool_wrapper.py     # Safe tool execution
├── tests/
│   ├── test_validator.py   # Validation tests
│   ├── test_repair_loop.py # Repair loop tests
│   └── test_tool_wrapper.py # Tool wrapper tests
├── fixtures/
│   └── bad_outputs/        # Examples of invalid outputs
├── examples/
│   ├── schema_validator.py
│   ├── repair_example.py
│   └── tool_execution.py
├── requirements.txt
├── pytest.ini
└── README.md
```

## Code Samples

### 1. Schema + Validator

See `src/schemas.py` and `src/validator.py` for:
- JSON Schema definitions using Pydantic
- Clear error reporting with path information
- Handling of common JSON parsing issues

### 2. Repair Loop

See `src/repair_loop.py` for:
- LLM call with validation
- Automatic retry on validation failure
- Error feedback to model
- Max retry limits (default 2)

### 3. Tool Execution Wrapper

See `src/tool_wrapper.py` for:
- Tool name allowlist
- Argument validation before execution
- Exception handling
- Typed error responses

## Testing

Run the test suite:

```bash
pytest
```

Run with coverage:

```bash
pytest --cov=src --cov-report=html
```

Run specific test file:

```bash
pytest tests/test_validator.py
```

## Bad Output Fixtures

The `fixtures/bad_outputs/` folder contains real examples of common LLM output failures:
- Trailing commas
- Missing fields
- Wrong types
- Invalid enums
- Extra text around JSON
- Malformed JSON

Use these to test your validation and repair logic.

## Best Practices

1. **Start with schemas**: Define output shape before writing prompts
2. **Validate strictly**: Check required fields, types, enums, formats
3. **Repair carefully**: Retry 1-2 times, then fail safely
4. **Log everything**: Track failures, repair attempts, success rates
5. **Test thoroughly**: Use golden cases, property-based tests, regression tests

## Security

- Always validate model output before use
- Use allowlists for tool names
- Never let model choose raw SQL, shell commands, or unconstrained URLs
- Treat model output as untrusted input

## License

This code is provided as example code for educational purposes.
