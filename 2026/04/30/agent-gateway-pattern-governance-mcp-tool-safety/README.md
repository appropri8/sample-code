# Agent Gateway Pattern: Governance, MCP, and Tool Safety

This sample implements a small Agent Gateway in dependency-free Python.

It shows how to keep agents from calling enterprise systems directly. The agent sends a tool invocation to the gateway. The gateway validates the payload, checks policy, handles approvals, routes to an MCP-style tool server, normalizes the result, and writes an audit record.

## Run the Demo

```bash
python3 -m agent_gateway.demo
```

The demo runs three calls:

1. Read order history, which is low risk and runs immediately.
2. Request a refund over the approval threshold, which returns `pending_approval`.
3. Approve the refund and execute it through the MCP broker.

## Run Tests

```bash
python3 -m unittest discover tests
```

## Project Structure

```text
.
├── agent_gateway/
│   ├── approvals.py      # Human approval records and payload binding
│   ├── audit.py          # Structured audit store
│   ├── demo.py           # Executable demo
│   ├── gateway.py        # Gateway orchestration
│   ├── mcp_broker.py     # MCP-style routing adapter
│   ├── policy.py         # Policy-as-code evaluator
│   ├── registry.py       # Tool registry loader
│   └── schema.py         # Small JSON schema validator
├── config/
│   ├── policies.json
│   └── tool_registry.json
└── tests/
    └── test_gateway.py
```

## Design Notes

- The MCP broker is intentionally local and small. It uses the same envelope shape you would send to an MCP `tools/call` handler, but it does not require an external MCP SDK.
- The gateway binds approvals to the exact tool name and argument fingerprint. An approval for one refund payload cannot be reused for a different amount.
- Audit records include allowed, denied, approval-required, and successful executions.
- The sample uses JSON config so it can run without third-party packages.

