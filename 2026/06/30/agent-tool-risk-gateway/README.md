# Tool-Risk Gateway

A reference implementation of a **tool-risk gateway** — a control plane that sits between AI agents and every external action they can take.

This is the accompanying code for the article **"The Agent Tool-Risk Gateway: Designing Approval, Policy, and Capability Boundaries Before Tool Execution"** (June 30, 2026).

## Architecture

```
Agent → Gateway → [Tool Registry → Policy Engine → Approval? → Token Issuer → Adapter] → Tool
```

The gateway intercepts every proposed tool call and decides:
- **Allow** — Execute immediately
- **Deny** — Reject with reason, log attempt
- **Require approval** — Pause for human-in-the-loop
- **Require sandbox** — Isolated execution

## Components

| Component | File | Purpose |
|---|---|---|
| Gateway service | `gateway.py` | FastAPI app with all endpoints |
| Agent simulator | `agent_simulator.py` | Demo client that tests all flows |
| Tests | `test_gateway.py` | 20+ tests covering policy, tokens, audit |
| Dependencies | `requirements.txt` | Python packages |

### Key Features

- **Risk classification** — Tools categorized by risk (read-only → financial)
- **Policy engine** — Role checks, schema validation, scope constraints
- **Capability tokens** — HMAC-signed, short-lived tokens scoped to one action + one resource
- **Approval engine** — Asynchronous HITL with timeout, escalation path
- **Dual approval** — Two humans required for high-risk actions
- **Audit logging** — Immutable, redacted, traceable logs
- **Metrics** — Auto-approve rate, deny rate, approval latency

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start the gateway
uvicorn gateway:app --reload --port 8000

# 3. In another terminal, run the demo
python agent_simulator.py
```

## Demo Scenarios

The agent simulator demonstrates 11 scenarios:

| # | Scenario | Expected Outcome |
|---|---|---|
| 1 | Health check | Gateway status |
| 2 | List registered tools | All 6 tools with risk class |
| 3 | Knowledge base search | Auto-approved (read-only) |
| 4 | CRM status update | Pending → approved by human |
| 5 | CRM update (wrong role) | Denied |
| 6 | Unknown tool | Denied |
| 7 | Payment charge | Pending approval (dual) |
| 8 | Invalid enum value | Denied (schema validation) |
| 9 | Audit log | Last 10 entries |
| 10 | Gateway metrics | Counts |
| 11 | Pending approvals | Current queue |

## API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Health check |
| GET | `/tools` | List all registered tools |
| POST | `/agent/propose-tool-call` | Agent proposes a tool call |
| POST | `/approve` | Human approves/rejects |
| GET | `/approvals/pending` | List pending approvals |
| GET | `/audit-log` | View audit log |
| GET | `/metrics` | Gateway metrics |

## Running Tests

```bash
pytest test_gateway.py -v
```

Tests cover:
- Policy evaluation (allow, deny, approval required)
- Schema validation (missing fields, invalid values)
- Role-based access control
- Capability token minting and verification
- Token expiry and tamper detection
- Sensitive field redaction
- Tool registry integrity

## Production Considerations

- Replace in-memory stores with a database
- Use environment variables for `GATEWAY_SECRET_KEY`
- Add real tool adapters (CRM SDK, email API, etc.)
- Integrate with a secret manager (HashiCorp Vault, AWS Secrets Manager)
- Add rate limiting and cost budgets
- Wire up Slack/Teams for approval notifications
- Add OpenTelemetry tracing for observability

## License

MIT
