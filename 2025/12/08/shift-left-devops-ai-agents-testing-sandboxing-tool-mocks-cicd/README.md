# Shift-Left DevOps for AI Agents

Complete executable code samples demonstrating shift-left DevOps practices for AI agents: testing, sandboxing, and tool mocks in CI/CD.

## Overview

This repository contains a complete implementation of shift-left DevOps practices for AI agents:

- **Contract Validation**: JSON Schema-based validation of agent actions
- **Tool Mocks**: Mock implementations of external tools for testing
- **Unit Tests**: Tests for tools, contracts, and agent behavior
- **Sandbox Scenarios**: Full agent runs against fixed scenarios
- **CI/CD Integration**: GitHub Actions pipeline with all checks
- **Policy Checks**: Automated policy validation

## Architecture

```
┌─────────────┐
│   Agent     │
│  (Core)     │
└──────┬──────┘
       │
       ├──► Tool Interface
       │    ├── Real Implementation
       │    └── Mock Implementation
       │
       ├──► Contract Validator
       │    └── JSON Schema + Policies
       │
       └──► Scenario Runner
            └── YAML Scenarios
```

## Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Run Tests

```bash
# Unit tests
pytest tests/

# With coverage
pytest tests/ --cov=src --cov-report=html
```

### Run Sandbox Scenarios

```bash
# Run all scenarios
python scripts/run_scenarios.py

# With mocks (default)
USE_MOCKS=true python scripts/run_scenarios.py
```

### Run Policy Checks

```bash
python scripts/check_policies.py
```

## Project Structure

```
.
├── src/
│   ├── __init__.py
│   ├── agent.py              # Agent implementation
│   ├── tools.py              # Tool interfaces and implementations
│   ├── contracts.py          # Contract definitions
│   └── contract_validator.py # Contract validation logic
├── tests/
│   ├── test_contracts.py     # Contract validation tests
│   ├── test_tools.py         # Tool tests
│   └── test_agent.py         # Agent tests
├── scenarios/
│   ├── forgot_password.yaml  # Password reset scenario
│   ├── search_user.yaml      # User search scenario
│   └── send_notification.yaml # Email notification scenario
├── scripts/
│   ├── run_scenarios.py      # Scenario runner
│   └── check_policies.py     # Policy checker
└── .github/
    └── workflows/
        └── ci.yml            # CI/CD pipeline
```

## Key Concepts

### 1. Contract Validation

Contracts define what agent actions are allowed:

```python
from src.contract_validator import validate_agent_action

action = {
    "tool_name": "search_database",
    "parameters": {"query": "find users", "limit": 10}
}

is_valid, errors = validate_agent_action(action)
```

### 2. Tool Mocks

Mock implementations for testing without real API calls:

```python
from src.tools import create_tools

# Use mocks
tools = create_tools(use_mocks=True)

# Or real implementations
tools = create_tools(use_mocks=False)
```

### 3. Sandbox Scenarios

YAML files defining test scenarios:

```yaml
name: "Search for user"
user_message: "Search for user1@example.com"
expected_tools:
  - name: "search_database"
max_steps: 3
```

### 4. Policy Checks

Automated policy validation:

- Max steps per conversation
- Forbidden tools in test environments
- Required parameters
- PII handling

## CI/CD Pipeline

The GitHub Actions pipeline runs:

1. **Lint**: Code formatting and style checks
2. **Unit Tests**: All unit tests with coverage
3. **Sandbox Scenarios**: Full agent runs against scenarios
4. **Policy Checks**: Policy validation

All stages must pass for a PR to be merged.

## Examples

### Example 1: Testing Tool Selection

```python
from src.agent import create_agent

agent = create_agent(use_mocks=True)
response = agent.process("Search for user1@example.com")

assert response["tool_calls"][0]["tool_name"] == "search_database"
```

### Example 2: Contract Validation

```python
from src.contract_validator import validate_agent_action

action = {
    "tool_name": "search_database",
    "parameters": {"query": "test", "limit": 10}
}

is_valid, errors = validate_agent_action(action)
assert is_valid
```

### Example 3: Running Scenarios

```bash
# Run all scenarios
python scripts/run_scenarios.py

# Output:
# PASS: User forgot password
# PASS: Search for user
# PASS: Send notification
# 
# Results: 3/3 scenarios passed
```

## Best Practices

1. **Always use mocks in CI**: Never call real APIs from tests
2. **Start with simple scenarios**: Add complexity gradually
3. **Validate contracts early**: Fail fast on invalid actions
4. **Keep scenarios focused**: One scenario per use case
5. **Version contracts**: Track changes over time
6. **Monitor policy violations**: Alert on dangerous operations

## Extending

### Adding a New Tool

1. Create interface in `src/tools.py`:
```python
class NewTool(ABC):
    @abstractmethod
    def do_something(self, param: str) -> dict:
        pass
```

2. Implement real and mock versions
3. Add to `create_tools()` function
4. Update contracts in `src/contracts.py`

### Adding a New Scenario

1. Create YAML file in `scenarios/`:
```yaml
name: "New scenario"
user_message: "User request"
expected_tools:
  - name: "new_tool"
max_steps: 5
```

2. Run scenarios to verify it works

### Adding a New Policy

1. Add to `POLICY_RULES` in `src/contracts.py`
2. Update `check_policy_violations()` in `src/contract_validator.py`
3. Add tests in `tests/test_contracts.py`

## Troubleshooting

### Scenarios Failing

- Check that expected tools match actual tool names
- Verify max_steps is appropriate
- Review error messages in scenario output

### Contract Validation Failing

- Check tool_name matches enum in contract
- Verify parameters match schema
- Review required parameters

### Policy Violations

- Check max_steps limit
- Verify no forbidden tools in test environment
- Review required parameters for each tool

## Resources

- [JSON Schema Documentation](https://json-schema.org/)
- [Pytest Documentation](https://docs.pytest.org/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)

## License

MIT
