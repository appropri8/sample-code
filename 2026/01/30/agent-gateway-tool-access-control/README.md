# Agent Gateway: Policy, Secrets, Audit

A Python/FastAPI implementation of an Agent Gateway that provides one outbound path for tool calls: policy (allowlist by role, deny by default), secrets (injected at execution time), and audit (structured logs with redaction).

## Overview

This repository implements the Agent Gateway pattern from the article "Put a Gateway in Front of Your Agents: Tool Access Control, Secrets, and Audit Trails." The gateway sits between agents and tools, enforcing:

- **Tool registry** — JSON schema validation, deny by default
- **Policy** — Per-tool allowlist by agent role, forbidden fields
- **Rate limiting** — Per-agent limits and timeouts
- **Audit** — Structured logs with redaction of secrets and PII
- **Approval flow** — Pending state for high-risk tools; human approves, gateway executes

## Requirements

- Python 3.11+
- pip

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

### 1. Start the Gateway

From the repo root (parent of `src`):

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be at `http://localhost:8000`. Docs: `http://localhost:8000/docs`.

### 2. Call a Tool (Signed Envelope)

Agents send a signed envelope: `agent_id`, `agent_version`, `request_id`, `tool`, `arguments`.

```bash
curl -X POST http://localhost:8000/api/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "agent_deploy_001",
    "agent_version": "1.2.0",
    "request_id": "req_uuid_123",
    "tool": "read_file",
    "arguments": {"path": "/workspace/readme.md"}
  }'
```

Response (success):

```json
{
  "success": true,
  "result": {"content": "[mock read of /workspace/readme.md]", "path": "/workspace/readme.md"},
  "audit_id": "audit_..."
}
```

### 3. Tool Requiring Approval

For tools like `write_file` or `delete_file`, the gateway returns `pending_approval` and an `approval_id`:

```bash
curl -X POST http://localhost:8000/api/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "agent_deploy_001",
    "agent_version": "1.2.0",
    "request_id": "req_uuid_456",
    "tool": "delete_file",
    "arguments": {"path": "/tmp/old.txt"}
  }'
```

Response:

```json
{
  "success": false,
  "status": "pending_approval",
  "approval_id": "approv_...",
  "error": "Human approval required",
  "audit_id": "audit_..."
}
```

Then approve:

```bash
curl -X POST http://localhost:8000/approve \
  -H "Content-Type: application/json" \
  -d '{"approval_id": "approv_...", "approved": true}'
```

### 4. Run Tests

```bash
# From repo root, with venv activated
pip install -r requirements.txt
pytest tests/ -v
```

## Project Structure

```
.
├── src/
│   ├── main.py              # FastAPI app: /api/tools/call, /approve
│   ├── models.py            # Signed envelope, response, approval
│   └── gateway/
│       ├── registry.py      # Tool registry + JSON schema validation
│       ├── policy.py        # Allowlist by role, forbidden fields, requires_approval
│       ├── rate_limit.py    # Per-agent rate limiting
│       ├── audit.py         # Structured audit logs with redaction
│       ├── approval.py      # Pending queue, approve, execute
│       └── executor.py       # Mock tool executor (secrets injected at execution)
├── policies/
│   └── tool_policy.rego     # OPA example: deny not on allowlist, forbid fields, require approval
├── tests/
│   ├── test_gateway.py      # Integration: call, approve, audit
│   ├── test_policy.py       # Policy and registry
│   └── test_audit_redaction.py  # Redaction of secrets/PII
├── requirements.txt
└── README.md
```

## Features

- **Signed envelope** — `agent_id`, `agent_version`, `request_id` for verification and tracing
- **Tool registry** — Deny by default; only registered tools with JSON schema are allowed
- **Policy** — Role-based allowlist; forbidden fields in arguments cause deny
- **Rate limiting** — Per-agent limits (configurable window and max calls)
- **Audit** — Every request/decision/outcome logged with redaction (API keys, passwords, email, SSN)
- **Approval flow** — High-risk tools (e.g. write_file, delete_file) go to pending; `/approve` executes

## OPA Policy Example

The `policies/tool_policy.rego` file shows an Open Policy Agent policy that:

- Denies tools not on the allowlist for the agent's role
- Denies requests containing forbidden fields (e.g. password, api_key)
- Marks tools that require approval (write_file, delete_file)

You can integrate OPA with the gateway by calling OPA for the `allow`/`deny` and `requires_approval` decisions instead of the inline Python policy.

## Related Article

See the blog article "Put a Gateway in Front of Your Agents: Tool Access Control, Secrets, and Audit Trails" for the full pattern, checklist, and reference architecture.
