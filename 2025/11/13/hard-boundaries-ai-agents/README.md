# Hard Boundaries for AI Agents

A Python library for enforcing hard boundaries on AI agents in production. This library provides time limits, step budgets, token budgets, cost tracking, tool permissions, and data boundaries to prevent runaway agent behavior.

## Features

- **Agent Contracts**: Define what agents can do with clear limits
- **Time Limits**: Enforce maximum runtime and step counts
- **Token Budgets**: Track and limit token usage
- **Cost Budgets**: Track and limit API costs
- **Tool Permissions**: Role-based and environment-based tool scoping
- **Data Boundaries**: PII redaction and data scoping
- **Bounded Agent Wrapper**: Combine all boundaries in one place

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

### Basic Usage

```python
from src.contracts import AgentContract
from src.bounded_agent import BoundedAgent, SimpleAgentCore

# Define contract
contract = AgentContract(
    name="support_bot",
    allowed_tools=["search_kb", "create_ticket"],
    max_runtime_seconds=30,
    max_steps=10,
    max_tokens=10000,
    max_cost_dollars=0.50,
    required_output="text"
)

# User context
user_context = {
    "user_id": "user_123",
    "tenant_id": "tenant_456",
    "role": "user",
    "environment": "production",
    "request_id": "req_789",
    "context": {}
}

# Create agent
agent_core = SimpleAgentCore()
agent = BoundedAgent(agent_core, contract, user_context)

# Run
result = agent.run("How do I reset my password?")

if result.get("error"):
    print(f"Error: {result['error']}")
else:
    print(f"Response: {result['response']}")
```

### Time and Step Limits

```python
from src.timeouts import StepBudget, timeout

# Step budget
budget = StepBudget(max_steps=10)
while budget.check():
    budget.use_step()
    # Do work

# Timeout
with timeout(30):
    result = long_running_operation()
```

### Token and Cost Budgets

```python
from src.budgets import TokenBudget, CostBudget

# Token budget
token_budget = TokenBudget(max_tokens=10000)
tokens = token_budget.count_tokens(text)
token_budget.add_tokens(tokens)

# Cost budget
cost_budget = CostBudget(max_cost_dollars=1.0)
cost_budget.add_cost("gpt-4", input_tokens=1000, output_tokens=500)
```

### Tool Permissions

```python
from src.permissions import get_tools_for_role, can_call_tool

# Get tools for role
tools = get_tools_for_role("user")

# Check if tool can be called
if can_call_tool("delete_ticket", "user", "production"):
    # Call tool
    pass
```

### Data Boundaries

```python
from src.data_boundaries import redact_pii, prepare_safe_input

# Redact PII
safe_text = redact_pii("Contact me at john@example.com")

# Prepare safe input
safe_input = prepare_safe_input(user_input, context)
```

## Examples

See the `examples/` directory for complete examples:

- `basic_agent.py`: Basic bounded agent usage
- `timeout_example.py`: Timeout and step budget examples
- `budget_example.py`: Token and cost budget examples
- `permissions_example.py`: Tool permission examples
- `data_boundaries_example.py`: PII redaction and data scoping examples

## Testing

Run the test suite:

```bash
pytest
```

Run with coverage:

```bash
pytest --cov=src --cov-report=html
```

## Architecture

### Components

1. **Contracts** (`src/contracts.py`): Define agent capabilities and limits
2. **Timeouts** (`src/timeouts.py`): Enforce time and step limits
3. **Budgets** (`src/budgets.py`): Track tokens and costs
4. **Permissions** (`src/permissions.py`): Manage tool access
5. **Data Boundaries** (`src/data_boundaries.py`): Handle PII and data scoping
6. **Bounded Agent** (`src/bounded_agent.py`): Wrapper that enforces all boundaries

## Design Principles

1. **Hard Boundaries**: Limits are enforced in code, not just prompts
2. **Fail Gracefully**: Return partial results when limits are hit
3. **Audit Trail**: Log all tool calls and boundary violations
4. **Minimum Access**: Agents only see tools they need
5. **Data Protection**: PII is redacted before reaching models

## Best Practices

1. **Start with Contracts**: Define what each agent can do
2. **Set Reasonable Limits**: Not too strict, not too loose
3. **Monitor Boundaries**: Track when limits are hit
4. **Adjust Gradually**: Add boundaries one at a time
5. **Test Boundaries**: Ensure limits work as expected

## Limitations

- Timeout implementation uses signals (Unix only)
- Token counting is approximate
- Cost estimates based on published pricing
- PII redaction uses simple regex patterns (use proper tools in production)

## Contributing

When adding features:

1. Add tests for new functionality
2. Update documentation
3. Consider security implications
4. Test with various boundary conditions

## License

This code is provided as example code for educational purposes. Adapt it to your specific requirements and use cases.

