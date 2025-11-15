# Tool-Safe AI Agents: Practical Guardrails for Real-World Integrations

A Python library demonstrating practical guardrails for AI agents that use tools. This implementation shows how to prevent agents from doing unsafe or surprising things when calling tools like email, payments, or internal APIs.

## Features

- **Tool Registry**: Metadata-driven tool definitions with risk levels, role permissions, and approval requirements
- **Policy Layer**: Wrapper that enforces guardrails on all tool calls
- **Schema Validation**: Strict validation of tool inputs using JSON schemas
- **Approval System**: Human-in-the-loop approval for high-risk actions
- **Red Team Testing**: Test harness for validating guardrails against attack prompts
- **Comprehensive Logging**: Audit trail for all tool calls and approvals

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

### Basic Usage

```python
from src.policy_layer import PolicyLayer

# Create policy layer for a support agent
policy = PolicyLayer(user_role="support_agent", user_id="user_123")

# Call a tool (will be validated and checked for permissions)
result = policy.call_tool_with_policy(
    tool_name="read_ticket",
    args={"ticket_id": "TKT-12345"},
    run_id="run_001"
)

print(result)
```

### Using the Support Agent

```python
from src.support_agent import SupportAgent

# Create agent
agent = SupportAgent(user_role="support_agent", user_id="agent_001")

# Handle a user request
result = agent.handle_user_request("read ticket TKT-12345")
print(result)
```

### Managing Approvals

```python
# List pending approvals
approvals = policy.get_pending_approvals()
for approval in approvals:
    print(f"Approval ID: {approval.approval_id}")
    print(f"Tool: {approval.tool_name}")
    print(f"Args: {approval.args}")

# Approve an action
result = policy.approve_action(
    approval_id="approval_abc123",
    reviewer_id="reviewer_001"
)
```

## Examples

### Example 1: Basic Policy Layer Usage

```bash
python examples/basic_usage.py
```

Shows how to use the policy layer to:
- Call allowed tools
- Handle permission denials
- Handle validation errors
- Request and process approvals

### Example 2: Support Agent

```bash
python examples/support_agent_example.py
```

Demonstrates a complete support agent that:
- Reads tickets
- Adds comments
- Handles approval requirements for high-risk actions

### Example 3: Approval CLI

```bash
# List pending approvals
python examples/approval_cli.py list

# Approve an action
python examples/approval_cli.py approve approval_abc123 reviewer_001

# Reject an action
python examples/approval_cli.py reject approval_abc123 "Not appropriate" reviewer_001
```

### Example 4: Red Team Testing

```bash
python examples/red_team_tests.py
```

Tests guardrails against malicious prompts to ensure:
- Permission checks work
- Validation prevents invalid inputs
- Approval is required for high-risk actions
- Dangerous actions are blocked

## Architecture

### Components

1. **Tool Registry** (`src/tool_registry.py`): Defines tools with metadata
   - Risk levels (low, medium, high)
   - Allowed roles
   - Approval requirements
   - JSON schemas for validation

2. **Validators** (`src/validators.py`): Schema validation
   - Required field checking
   - Type checking
   - String constraint validation
   - Comprehensive validation using jsonschema

3. **Policy Layer** (`src/policy_layer.py`): Enforces guardrails
   - Permission checking
   - Schema validation
   - Approval request handling
   - Tool execution
   - Logging

4. **Approval System** (`src/approvals.py`): Manages approvals
   - Approval request storage
   - Approval/rejection tracking
   - Querying pending approvals

5. **Support Agent** (`src/support_agent.py`): Example agent implementation
   - Tool calling through policy layer
   - User request handling
   - Approval management

## Design Principles

### 1. Least Privilege

Each agent run has a capability set based on user role. Tools are filtered by:
- User role
- Tool permissions
- Environment settings

### 2. Strict Validation

All tool inputs are validated against JSON schemas before execution:
- Required fields
- Type checking
- Value constraints
- Business rules

### 3. Approval Gates

High-risk tools require human approval:
- Threshold-based (amount, records affected)
- Context-based (VIP customers, new accounts)
- Clear explanations for reviewers

### 4. Comprehensive Logging

Every tool call is logged with:
- User ID (hashed)
- Tool name and parameters
- Approval status
- Timestamps
- Sensitive data redaction

## Testing

Run the test suite:

```bash
pytest
```

Run with coverage:

```bash
pytest --cov=src --cov-report=html
```

Run red team tests:

```bash
python examples/red_team_tests.py
```

## Tool Registry Structure

Tools are defined with the following metadata:

```python
Tool(
    name="close_ticket",
    description="Close a support ticket",
    schema={...},  # JSON schema
    risk_level=RiskLevel.HIGH,
    allowed_roles=["support_manager"],
    requires_approval=True
)
```

## Adding New Tools

1. Define the tool in `src/tool_registry.py`:

```python
TOOL_REGISTRY["new_tool"] = Tool(
    name="new_tool",
    description="Description of the tool",
    schema={
        "type": "object",
        "properties": {
            "param1": {"type": "string"}
        },
        "required": ["param1"]
    },
    risk_level=RiskLevel.LOW,
    allowed_roles=["support_agent"]
)
```

2. Implement the tool execution in `PolicyLayer._execute_tool()`

3. Add tests in `tests/`

## Best Practices

1. **Start with Least Privilege**: Only grant the minimum tools needed
2. **Validate Everything**: Use strict schemas for all tool inputs
3. **Require Approval for High-Risk Actions**: Don't trust agents with destructive operations
4. **Log Everything**: Maintain audit trails for debugging and compliance
5. **Test Guardrails**: Use red team prompts to validate defenses
6. **Monitor in Production**: Watch for blocked calls and adjust thresholds

## Limitations

- Simple in-memory approval queue (extend for production)
- Basic tool execution simulation (implement real tool calls)
- No distributed tracing (single-process only)
- Basic PII redaction (enhance for your needs)

## Contributing

When adding features:

1. Add tests for new functionality
2. Update documentation
3. Follow existing code patterns
4. Run red team tests to ensure guardrails still work

## License

This code is provided as example code for educational purposes. Adapt it to your specific requirements and use cases.

