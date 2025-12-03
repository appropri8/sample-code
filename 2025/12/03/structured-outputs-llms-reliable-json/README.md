# Structured Outputs with LLMs: Reliable JSON Every Time

Complete executable code samples demonstrating how to turn a chatty LLM into a safe JSON-producing service that other systems can trust.

## Overview

This repository contains implementations of structured output patterns for LLMs:

- **Schema-First Design**: Define schemas before prompts
- **Robust Parsing**: Extract JSON from mixed text responses
- **Strong Validation**: Validate against schemas with detailed error messages
- **Smart Retries**: Retry with error feedback when parsing/validation fails
- **Observability**: Logging and metrics for production systems
- **Auto-Repair**: Fix common JSON issues without retrying

Both Python and TypeScript implementations are provided.

## Installation

### Python

```bash
cd python
pip install -r requirements.txt
```

### TypeScript

```bash
cd typescript
npm install
npm run build
```

## Prerequisites

- Python 3.10+ (for Python examples)
- Node.js 18+ (for TypeScript examples)
- OpenAI API key (set `OPENAI_API_KEY` environment variable)
- Optional: Redis (for distributed rate limiting in observability examples)

## Quick Start

### Python Example

```bash
cd python
export OPENAI_API_KEY=your-key-here
python examples/task_triage_example.py
```

### TypeScript Example

```bash
cd typescript
export OPENAI_API_KEY=your-key-here
npm run dev -- examples/task-triage-example.ts
```

## Structure

```
.
├── python/
│   ├── src/
│   │   ├── schema.py              # Schema definitions with Pydantic
│   │   ├── prompt_builder.py      # Build prompts from schemas
│   │   ├── parser.py              # Extract JSON from raw responses
│   │   ├── validator.py           # Validate against schemas
│   │   ├── retry.py               # Retry logic with error feedback
│   │   ├── repair.py              # Auto-repair common JSON issues
│   │   ├── llm_client.py          # LLM client wrapper
│   │   ├── observability.py       # Logging and metrics
│   │   └── structured_output.py   # Complete structured output pipeline
│   ├── examples/
│   │   ├── task_triage_example.py  # Complete task triage API example
│   │   ├── parsing_example.py      # JSON parsing examples
│   │   ├── validation_example.py  # Schema validation examples
│   │   └── retry_example.py        # Retry strategy examples
│   └── requirements.txt
│
├── typescript/
│   ├── src/
│   │   ├── schema.ts              # Schema definitions with Zod
│   │   ├── prompt-builder.ts       # Build prompts from schemas
│   │   ├── parser.ts              # Extract JSON from raw responses
│   │   ├── validator.ts           # Validate against schemas
│   │   ├── retry.ts               # Retry logic with error feedback
│   │   ├── repair.ts              # Auto-repair common JSON issues
│   │   ├── llm-client.ts          # LLM client wrapper
│   │   ├── observability.ts       # Logging and metrics
│   │   └── structured-output.ts   # Complete structured output pipeline
│   ├── examples/
│   │   ├── task-triage-example.ts  # Complete task triage API example
│   │   ├── parsing-example.ts      # JSON parsing examples
│   │   ├── validation-example.ts   # Schema validation examples
│   │   └── retry-example.ts        # Retry strategy examples
│   ├── package.json
│   └── tsconfig.json
│
└── README.md
```

## Key Patterns

### 1. Schema-First Design

Define schemas before writing prompts. Use the schema to generate the prompt.

**Python:**
```python
from pydantic import BaseModel
from enum import Enum

class Category(str, Enum):
    BUG = "bug"
    FEATURE = "feature"

class TaskTriage(BaseModel):
    category: Category
    priority: int
```

**TypeScript:**
```typescript
import { z } from 'zod';

const TaskTriageSchema = z.object({
  category: z.enum(['bug', 'feature']),
  priority: z.number().int().min(1).max(5),
});
```

### 2. Robust Parsing

Extract JSON from responses that might include markdown, explanations, or extra text.

```python
from src.parser import extract_json

raw_response = """Here's the JSON:
```json
{"category": "bug", "priority": 3}
```"""

json_data = extract_json(raw_response)  # Returns {"category": "bug", "priority": 3}
```

### 3. Strong Validation

Validate parsed JSON against your schema with detailed error messages.

```python
from src.validator import validate_json
from src.schema import TaskTriage

json_data = {"category": "bug", "priority": 3}
result = validate_json(json_data, TaskTriage)  # Returns TaskTriage instance
```

### 4. Smart Retries

Retry with error feedback when parsing or validation fails.

```python
from src.structured_output import get_structured_output

result = get_structured_output(
    llm=llm_client,
    prompt=prompt,
    schema=TaskTriage,
    max_retries=3
)
```

### 5. Auto-Repair

Fix common JSON issues without retrying.

```python
from src.repair import repair_json

broken_json = '{"key": "value",}'  # Trailing comma
fixed = repair_json(broken_json)  # Returns {"key": "value"}
```

### 6. Observability

Log everything. Track metrics. Alert on issues.

```python
from src.observability import log_structured_output_call, track_metrics

log_structured_output_call(
    prompt_hash="abc123",
    raw_response=response,
    parsed_json=json_data,
    success=True,
    duration_ms=1500
)
```

## Examples

### Task Triage API

Complete example of a task triage API that categorizes and prioritizes issues.

**Python:**
```bash
cd python
python examples/task_triage_example.py
```

**TypeScript:**
```bash
cd typescript
npm run dev -- examples/task-triage-example.ts
```

### Parsing Examples

Demonstrates extracting JSON from various response formats.

**Python:**
```bash
python examples/parsing_example.py
```

**TypeScript:**
```bash
npm run dev -- examples/parsing-example.ts
```

### Validation Examples

Shows schema validation with detailed error messages.

**Python:**
```bash
python examples/validation_example.py
```

**TypeScript:**
```bash
npm run dev -- examples/validation-example.ts
```

### Retry Examples

Demonstrates retry strategies with error feedback.

**Python:**
```bash
python examples/retry_example.py
```

**TypeScript:**
```bash
npm run dev -- examples/retry-example.ts
```

## Testing

### Python

```bash
cd python
pytest tests/
```

### TypeScript

```bash
cd typescript
npm test
```

## Environment Variables

```bash
# Required
OPENAI_API_KEY=your-openai-api-key

# Optional (for observability examples)
REDIS_HOST=localhost
REDIS_PORT=6379
```

## Best Practices

1. **Define schema first** - Don't write prompts before schemas
2. **Use type-safe schemas** - Pydantic, Zod, etc.
3. **Forbid extra fields** - Reject fields you didn't ask for
4. **Version schemas** - Breaking changes need versioning
5. **Parse carefully** - Handle markdown, extra text, etc.
6. **Validate strictly** - Fail fast on invalid data
7. **Retry with feedback** - Tell the model what went wrong
8. **Log everything** - Raw responses, parsed JSON, errors
9. **Track metrics** - Parse errors, validation errors, response time
10. **Alert on issues** - High error rates, response time degradation

## Production Checklist

- [ ] Schema defined and versioned
- [ ] Prompts generated from schemas
- [ ] Parsing handles edge cases
- [ ] Validation with detailed errors
- [ ] Retry logic with error feedback
- [ ] Logging raw responses on failures
- [ ] Metrics for parse/validation errors
- [ ] Alerts on error rate increases
- [ ] Timeout handling
- [ ] Error messages are clear

## License

MIT

