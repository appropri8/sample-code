# Agent Mesh Interop: MCP for Tools + A2A for Agent-to-Agent

Complete executable code samples demonstrating how to build an agent mesh using MCP (Model Context Protocol) for tool connectivity and A2A (Agent-to-Agent) for agent communication.

## Overview

This repository contains working examples of:

- **Message Envelope Schema**: Standard format for all agent communication
- **Gateway Middleware**: Policy enforcement, budget tracking, and tool allowlists
- **MCP Tool Server & Client**: Tool connectivity using Model Context Protocol
- **A2A Message Handler**: Agent-to-agent communication routing
- **Loop Guard**: Prevention of infinite delegation loops

## Architecture

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   Agent A   │ ──A2A──>│   Gateway    │ ──MCP──>│   Tool X    │
└─────────────┘         │              │         └─────────────┘
                        │  - Policies  │
┌─────────────┐         │  - Budgets   │         ┌─────────────┐
│   Agent B   │ ──A2A──>│  - Routing   │ ──MCP──>│   Tool Y    │
└─────────────┘         └──────────────┘         └─────────────┘
```

## Prerequisites

- Node.js 18+ installed
- TypeScript 5.0+
- npm installed

## Installation

```bash
npm install
```

## Quick Start

### 1. Build the Project

```bash
npm run build
```

### 2. Run Examples

```bash
# Example 1: Message envelope schema
npm run example:envelope

# Example 2: Gateway middleware
npm run example:gateway

# Example 3: MCP tool server and client
npm run example:mcp

# Example 4: A2A message handler
npm run example:a2a

# Example 5: Loop guard
npm run example:loop
```

## Repository Structure

```
.
├── README.md
├── package.json
├── tsconfig.json
├── src/
│   ├── types.ts                    # Message envelope and type definitions
│   ├── gateway/
│   │   ├── middleware.ts           # Gateway policy enforcement
│   │   └── loop-guard.ts          # Infinite loop prevention
│   ├── mcp/
│   │   ├── tool-server.ts          # MCP tool server implementation
│   │   └── tool-client.ts          # MCP tool client implementation
│   ├── a2a/
│   │   └── message-handler.ts      # A2A message routing and dispatch
│   └── examples/
│       ├── message-envelope-example.ts
│       ├── gateway-example.ts
│       ├── mcp-example.ts
│       ├── a2a-example.ts
│       └── loop-guard-example.ts
└── dist/                           # Compiled JavaScript (generated)
```

## Key Concepts

### 1. Message Envelope

All agent communication uses a standard envelope format that includes:
- `trace_id`: Distributed tracing identifier
- `tenant_id`: Multi-tenancy support
- `auth`: Authentication tokens
- `budget`: Token and time budgets
- `source_agent` / `target_agent`: Routing information
- `delegation_depth`: Loop prevention

### 2. Gateway Middleware

The gateway enforces:
- **Trace ID propagation**: Ensures all requests have trace IDs
- **Tool allowlists**: Per-agent tool access control
- **Budget limits**: Token and time budget enforcement
- **Delegation depth**: Prevents infinite loops
- **Policy checks**: RBAC/ABAC access control

### 3. MCP Tool Server

Tools expose their capabilities via MCP:
- Tool discovery (`tools/list`)
- Tool execution (`tools/call`)
- Standardized input/output schemas
- Version management

### 4. A2A Message Handler

Agents communicate via A2A protocol:
- Message routing through gateway
- Agent discovery and dispatch
- Response envelope creation
- Context preservation

### 5. Loop Guard

Prevents infinite delegation:
- Maximum depth tracking (default: 5)
- Circular path detection
- Task-based deduplication
- TTL-based cleanup

## Examples

### Example 1: Message Envelope

```typescript
const envelope = createMessageEnvelope(
  'agent-a',
  'agent-b',
  {
    type: 'request',
    task_id: 'task-123',
    action: 'process_order',
    parameters: { order_id: 'order-456' },
  },
  {
    traceId: 'trace-abc-123',
    maxTokens: 1000,
    maxTimeMs: 5000,
  }
);
```

### Example 2: Gateway Middleware

```typescript
const gateway = new GatewayMiddleware(registry, policyEngine, budgetTracker);
const processed = await gateway.processRequest(envelope);
// Gateway validates:
// - Trace ID exists
// - Agent has access to requested tool
// - Budget limits not exceeded
// - Delegation depth within limits
```

### Example 3: MCP Tool Server

```typescript
const server = new MCPToolServer();
server.registerTool({
  name: 'calculator',
  description: 'Performs arithmetic',
  inputSchema: { /* ... */ },
  handler: async (args) => { /* ... */ },
});

const client = new MCPToolClient(transport);
const result = await client.callTool('calculator', {
  operation: 'add',
  a: 10,
  b: 5,
});
```

### Example 4: A2A Message Handler

```typescript
const handler = new A2AMessageHandler(registry, gateway);
const response = await handler.handleMessage(envelope);
// Handler:
// - Routes through gateway
// - Dispatches to target agent
// - Creates response envelope
// - Preserves context
```

### Example 5: Loop Guard

```typescript
const guard = new LoopGuard();
guard.checkLoop(envelope); // Validates depth and circular paths
const incremented = guard.incrementDepth(envelope);
```

## Failure Modes Addressed

1. **Tool Overload**: Gateway filters tool catalogs by allowlist
2. **Prompt Injection**: Gateway sanitizes tool outputs (implementation needed)
3. **Infinite Loops**: Loop guard tracks depth and circular paths
4. **Wrong Results**: Verification agents or schema validation (implementation needed)

## What MCP and A2A Solve

**MCP solves:**
- Tool discovery and versioning
- Standard tool call protocol
- Tool isolation and permissions

**A2A solves:**
- Agent-to-agent messaging
- Secure agent communication
- Task delegation between agents

**What you still need:**
- Authentication system
- Quota management
- Audit logging
- Distributed tracing

## Best Practices

1. **Always use the gateway**: All traffic should go through the gateway
2. **Set budgets early**: Define token and time budgets in message envelopes
3. **Track delegation depth**: Use loop guard to prevent infinite loops
4. **Filter tool catalogs**: Only show agents tools they're allowed to use
5. **Monitor failure modes**: Watch for tool overload, injection, loops, wrong results

## Related Article

This code accompanies the article: "Agent Mesh Interop: MCP for Tools + A2A for Agent-to-Agent (Without Building a Hairball)"

## License

MIT

