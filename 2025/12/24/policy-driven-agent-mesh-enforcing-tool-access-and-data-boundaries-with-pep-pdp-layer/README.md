# Policy-Driven Agent Mesh: PEP/PDP Implementation

Complete executable code sample demonstrating policy enforcement in an agent mesh system using PEP (Policy Enforcement Point) and PDP (Policy Decision Point) pattern.

## Overview

This repository contains a working implementation of policy-driven access control for multi-agent systems:

- **PEP (Policy Enforcement Point)**: Intercepts tool calls, extracts context, calls PDP, applies constraints
- **PDP (Policy Decision Point)**: Evaluates policies, returns allow/deny decisions with constraints
- **Policy Models**: Rego-style policies for tool access, tenant isolation, and data boundaries
- **Audit Logging**: Complete audit trail with trace IDs for correlation
- **Tenant Guard**: Enforces tenant isolation at the tool level

## Architecture

```
Agent Request
    ↓
PEP (extract context, call PDP, apply constraints)
    ↓
PDP (evaluate policies, return decision)
    ↓
Tool Execution (if allowed, with constraints)
    ↓
Audit Log (decision + trace_id)
```

## Prerequisites

- Python 3.8+
- pip

## Installation

1. Clone this repository

2. Install Python dependencies:

```bash
pip install -r requirements.txt
```

## Quick Start

Run the demo:

```bash
python examples/run_demo.py
```

You should see output like:

```
✓ Request 1 allowed: Support agent can read orders
✗ Request 2 denied: Policy denied: User does not have finance_role
✗ Request 3 denied: Cross-tenant access denied: request tenant acme-corp does not match query tenant competitor-corp

Audit Log:
  1234567890: allow - ReadOrders
  1234567891: deny - IssueRefund
  1234567892: deny - ReadOrders
```

## Repository Structure

```
.
├── README.md
├── requirements.txt
├── src/
│   ├── pep/
│   │   ├── __init__.py
│   │   ├── middleware.py          # PEP middleware
│   │   ├── pdp_client.py          # PDP client (simple implementation)
│   │   ├── audit_logger.py         # Audit logging
│   │   ├── cache.py               # Decision caching
│   │   └── break_glass.py         # Break-glass mode
│   ├── policies/
│   │   ├── __init__.py
│   │   ├── policy_engine.py       # Policy evaluation engine
│   │   └── policies.rego          # Rego-style policies (example)
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── read_orders_tool.py    # ReadOrders tool with tenant guard
│   │   ├── issue_refund_tool.py   # IssueRefund tool
│   │   ├── export_csv_tool.py     # ExportCSV tool
│   │   └── tenant_guard.py        # Tenant isolation enforcement
│   └── storage/
│       ├── __init__.py
│       └── memory_log_store.py    # In-memory audit log store
├── examples/
│   ├── __init__.py
│   └── run_demo.py                 # Demo script
└── tests/
    ├── __init__.py
    ├── test_pep.py                 # PEP tests
    ├── test_pdp.py                 # PDP tests
    └── test_tenant_guard.py        # Tenant guard tests
```

## Components

### PEP Middleware

The PEP intercepts tool calls and enforces policies:

```python
from src.pep.middleware import PEPMiddleware

pep = PEPMiddleware(pdp_client, audit_logger)
constrained_request = pep.enforce(request, trace_id="trace-123")
```

### PDP Client

The PDP evaluates policies and returns decisions:

```python
from src.pep.pdp_client import PDPClient

pdp = PDPClient()
decision = pdp.evaluate(context)
# Returns: {"decision": "allow", "constraints": {...}, "reason": "..."}
```

### Policy Engine

Simple policy engine that evaluates policies:

```python
from src.policies.policy_engine import PolicyEngine

engine = PolicyEngine()
engine.load_policies("src/policies/policies.rego")
decision = engine.evaluate(context)
```

### Tenant Guard

Enforces tenant isolation:

```python
from src.tools.tenant_guard import TenantGuard

guard = TenantGuard()
safe_params = guard.enforce_tenant_isolation(
    request_tenant_id="acme-corp",
    query_params={"tenant_id": "acme-corp"},
    tool_name="ReadOrders"
)
```

## Policy Examples

### Allow ReadOrders for support role

```python
{
    "condition": {
        "tool_name": "ReadOrders",
        "operation": "read",
        "tenant_match": True,
        "roles": ["support_role"]
    },
    "decision": "allow",
    "constraints": {
        "field_masking": ["email"]
    }
}
```

### Deny IssueRefund without finance_role

```python
{
    "condition": {
        "tool_name": "IssueRefund",
        "operation": "write",
        "roles": ["support_role"]  # Missing finance_role
    },
    "decision": "deny",
    "reason": "User does not have finance_role"
}
```

### Deny cross-tenant access

```python
{
    "condition": {
        "tool_name": "ReadOrders",
        "request_tenant": "acme-corp",
        "query_tenant": "competitor-corp"  # Mismatch!
    },
    "decision": "deny",
    "reason": "Cross-tenant access denied"
}
```

## Running Tests

```bash
python -m pytest tests/
```

## Integration with OpenTelemetry

This implementation pairs well with OpenTelemetry tracing. Include `trace_id` in audit logs to correlate policy decisions with distributed traces.

See the companion article: "Multi-Agent Mesh Observability: Tracing One Task Across 5 Agents with OpenTelemetry"

## Production Considerations

- **PDP Latency**: Cache decisions with short TTL (60 seconds)
- **Audit Log Storage**: Use time-series database or log aggregation system
- **Policy Versioning**: Store policies in Git, review changes via PR
- **Break-Glass Mode**: Require admin approval, time-limited, fully audited
- **Monitoring**: Alert on high deny rates, monitor PDP latency (p95 < 50ms)

## License

MIT

