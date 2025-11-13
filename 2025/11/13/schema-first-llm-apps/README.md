# Schema-First LLM Apps

A Python library demonstrating schema-first design for LLM applications. This library shows how to treat LLMs as strict, structured components instead of free-form text generators.

## Overview

Schema-first design means starting with the expected output shape (JSON schemas, Pydantic models) before writing prompts. This approach provides:

- **Stronger contracts**: Model must return valid JSON matching your schema
- **Easier testing**: Test schemas independently, validate outputs before use
- **Safer integration**: External systems get structured data, not free-form text
- **Tool safety**: Validate arguments before executing tools

## Features

- **Schema Definitions**: Pydantic models for common patterns (routers, extractors, summarizers)
- **LLM Client**: Client with automatic retry on validation failures
- **Tool Execution**: Safe tool execution with argument validation
- **Extractors**: Reusable patterns for entity extraction, summarization, contact extraction
- **Router**: Pattern for routing requests to appropriate handlers
- **Orchestrator**: End-to-end flow demonstrating schema-first architecture

## Installation

```bash
pip install -r requirements.txt
```

Set your OpenAI API key:

```bash
export OPENAI_API_KEY="your-api-key-here"
```

Or create a `.env` file:

```
OPENAI_API_KEY=your-api-key-here
```

## Quick Start

### Basic Extraction

```python
from src.llm_client import LLMClient
from src.schemas import TicketClassification

client = LLMClient()

classification = client.call_with_schema(
    "Classify this ticket: My payment failed and I need a refund.",
    TicketClassification
)

print(f"Intent: {classification.intent}")
print(f"Priority: {classification.priority}")
print(f"Tags: {classification.tags}")
```

### Router Pattern

```python
from src.router import Router
from src.llm_client import LLMClient

client = LLMClient()
router = Router(client)

result = router.route("I need help with my billing issue")
print(f"Route: {result.route}")
print(f"Confidence: {result.confidence}")
```

### Tool Execution

```python
from src.tools import tool_execution_wrapper, GetUserInfoArgs, get_user_info

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

### End-to-End Orchestrator

```python
from src.orchestrator import Orchestrator

orchestrator = Orchestrator()

result = orchestrator.process_request(
    "I need help with my billing issue",
    user_id="user123"
)

print(f"Route: {result['route']}")
print(f"Result: {result['result']}")
```

## Examples

### Basic Extraction

See `examples/basic_extraction.py` for examples of:
- Classifying support tickets
- Extracting contact information
- Handling missing data with nullable fields

### Router

See `examples/router_example.py` for routing requests to appropriate handlers.

### Tool Calling

See `examples/tool_calling_example.py` for:
- Executing tools with validation
- Handling validation failures
- Safe tool execution patterns

### Orchestrator

See `examples/orchestrator_example.py` for a complete end-to-end flow.

### Retry Logic

See `examples/retry_example.py` for automatic retry on validation failures.

## Architecture

### Components

1. **Schemas** (`src/schemas.py`): Pydantic models for structured outputs
2. **LLM Client** (`src/llm_client.py`): Client with schema validation and retry logic
3. **Tools** (`src/tools.py`): Tool execution with argument validation
4. **Extractors** (`src/extractors.py`): Reusable extraction patterns
5. **Router** (`src/router.py`): Request routing pattern
6. **Orchestrator** (`src/orchestrator.py`): End-to-end flow orchestration

### Schema Patterns

#### Router Pattern

Routes requests to appropriate handlers:

```python
class RouterOutput(BaseModel):
    route: Literal["billing", "tech_support", "sales", "other"]
    confidence: float
    reasoning: str
```

#### Extractor Pattern

Extracts structured data from unstructured text:

```python
class EntityExtraction(BaseModel):
    entities: List[dict]
    dates: List[str]
    decisions: List[str]
```

#### Summarizer Pattern

Generates structured summaries:

```python
class StructuredSummary(BaseModel):
    title: str
    summary: str
    risks: List[str]
    next_actions: List[str]
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

1. **Start with schemas**: Define output shape before writing prompts
2. **Use enums**: Constrain model output to fixed values
3. **Nullable fields**: Use Optional for "unknown" instead of forcing guesses
4. **Add descriptions**: Help the model understand what each field means
5. **Always validate**: Validate all LLM outputs before use
6. **Retry on failure**: Automatically retry with error feedback
7. **Validate tool args**: Check types, ranges, and permissions before execution

## Design Principles

This library demonstrates:

1. **Schema-first design**: Define schemas before prompts
2. **Strong validation**: Always validate outputs against schemas
3. **Safe tool execution**: Validate arguments before calling tools
4. **Graceful degradation**: Fallback and escalation on failures
5. **Reusable patterns**: Common patterns for routing, extraction, summarization

## Limitations

- Simple retry logic (extend for production needs)
- Basic error handling (add more sophisticated fallbacks)
- Example tool functions (replace with real implementations)
- No caching (add caching for production)

## Contributing

When adding features:

1. Add Pydantic schemas for new patterns
2. Write tests for new functionality
3. Update documentation
4. Follow existing code patterns
5. Consider validation and error handling

## License

This code is provided as example code for educational purposes. Adapt it to your specific requirements and use cases.

