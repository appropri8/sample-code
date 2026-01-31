# Least-Privilege MCP Agents

Complete executable code samples for the article "Least-Privilege MCP Agents: Capability Tokens, Tool Scopes, and a Policy Gate That Stops Bad Tool Calls".

## Overview

This repository demonstrates a security architecture for MCP (Model Context Protocol) agents using:
- Tool scopes with resource constraints
- Capability tokens (JWT-based)
- Policy gate for authorization
- Audit logging
- Defense against prompt injection

## Structure

```
.
├── src/
│   ├── 1-tool-registry.ts          # Tool definitions with scopes
│   ├── 2-capability-tokens.ts      # Token minting and verification
│   ├── 3-policy-evaluator.ts      # Policy rules and evaluation
│   ├── 4-tool-interceptor.ts      # Client-side enforcement
│   ├── 5-server-enforcement.ts    # Server-side enforcement
│   ├── 6-audit-logging.ts         # Logging and queries
│   └── 7-integration.ts           # Full integration example
├── tests/
│   ├── policy.test.ts             # Unit tests for policy rules
│   ├── injection.test.ts          # Injection defense tests
│   └── fuzzing.test.ts            # Fuzzing tests
├── package.json
├── tsconfig.json
└── README.md
```

## Installation

```bash
npm install
```

## Running Examples

### 1. Tool Registry with Scopes

```bash
npm run example:registry
```

Shows tool definitions with read/write scopes and resource constraints.

### 2. Capability Tokens

```bash
npm run example:tokens
```

Demonstrates token minting, verification, and expiration.

### 3. Policy Evaluator

```bash
npm run example:policy
```

Shows policy evaluation with different scenarios (allow, deny, require approval, downgrade).

### 4. Tool Call Interceptor

```bash
npm run example:interceptor
```

Demonstrates client-side enforcement with token validation.

### 5. Server-Side Enforcement

```bash
npm run example:server
```

Shows server-side token verification and resource matching.

### 6. Audit Logging

```bash
npm run example:audit
```

Demonstrates logging and querying policy decisions.

### 7. Full Integration

```bash
npm run example:integration
```

Complete end-to-end example with agent, policy gate, and MCP server.

## Running Tests

```bash
# All tests
npm test

# Unit tests only
npm run test:unit

# Injection tests
npm run test:injection

# Fuzzing tests
npm run test:fuzzing

# Watch mode
npm run test:watch
```

## Key Concepts

### Tool Scopes

Tools are classified by scope (read/write) and resource constraints:

```typescript
const TOOL_REGISTRY = {
  "repo.read": {
    scope: "read",
    resource_constraint: "path_prefix",
    allowed_prefixes: ["/src", "/docs"],
  },
  "repo.write": {
    scope: "write",
    resource_constraint: "path_prefix",
    allowed_prefixes: ["/src"],
    requires_approval: true,
  },
};
```

### Capability Tokens

JWT tokens with specific claims:

```typescript
interface CapabilityToken {
  sub: string;          // User ID
  run_id: string;       // Agent run ID
  tool: string;         // Tool name
  scope: string;        // Scope (read/write)
  resource: string;     // Resource constraint
  exp: number;          // Expiration
  nonce: string;        // Unique nonce
}
```

### Policy Gate

Evaluates every tool call request:

```typescript
function evaluatePolicy(request: PolicyRequest): PolicyResult {
  // Check tool scope, resource constraints, user permissions, risk tier
  // Return: allow, deny, require_approval, or downgrade
}
```

### Audit Logging

Every decision is logged:

```typescript
{
  timestamp: "2026-01-21T10:30:00Z",
  user_id: "user-123",
  run_id: "run-456",
  tool: "repo.write",
  decision: "allow",
  reason: "Request meets all policy requirements",
  rule_id: "rule-000"
}
```

## Security Features

### 1. Scoped Permissions

Tools can only access allowed resources:
- `repo.read` can only read from `/src` or `/docs`
- `repo.write` can only write to `/src`
- Path traversal attempts are blocked

### 2. Capability Tokens

- Short-lived (5 minutes default)
- Specific to one tool, one resource, one run
- Signed and verified
- Revocable via allowlist

### 3. Policy Gate

- Intercepts all tool calls
- Evaluates against policy rules
- Logs all decisions
- Supports approval workflows

### 4. Defense Against Injection

- Blocks dangerous tools for high-risk runs
- Requires approval for write operations
- Detects tool chaining patterns
- Validates resource constraints

## Example Scenarios

### Scenario 1: Legitimate Read

```typescript
// Agent wants to read a file
const request = {
  user_id: "user-123",
  run_id: "run-456",
  tool: "repo.read",
  resource: "/src/main.ts",
  run_risk_tier: "low",
};

// Policy evaluates: ALLOW
// Token minted: valid for 5 minutes
// Tool call succeeds
```

### Scenario 2: Blocked Injection

```typescript
// Malicious prompt tries to delete files
const request = {
  user_id: "user-123",
  run_id: "run-789",
  tool: "repo.delete",
  resource: "/",
  run_risk_tier: "high",
};

// Policy evaluates: DENY
// Reason: "Dangerous tool not allowed for high-risk runs"
// Tool call blocked
```

### Scenario 3: Approval Required

```typescript
// Agent wants to write a file
const request = {
  user_id: "user-123",
  run_id: "run-456",
  tool: "repo.write",
  resource: "/src/config.ts",
  run_risk_tier: "low",
};

// Policy evaluates: REQUIRE_APPROVAL
// Request queued for human review
// Agent waits for approval
```

### Scenario 4: Downgrade

```typescript
// Medium-risk run tries to write
const request = {
  user_id: "user-123",
  run_id: "run-456",
  tool: "repo.write",
  resource: "/src/main.ts",
  run_risk_tier: "medium",
};

// Policy evaluates: DOWNGRADE
// Alternative: repo.read
// Token minted for read-only access
```

## Metrics

The implementation tracks:
- Permission minimization: 90%+ of calls use minimal scopes
- Overhead: <10ms per policy evaluation
- False positives: <5% of legitimate calls denied

## Production Considerations

### 1. Token Storage

In production, store tokens in:
- Redis for fast lookup
- Database for audit trail
- Memory for short-term cache

### 2. Logging

Send logs to:
- Structured logging service (e.g., Elasticsearch)
- SIEM for security monitoring
- Audit database for compliance

### 3. Approval Workflows

Integrate with:
- Slack/Teams for notifications
- Ticketing system for tracking
- Admin dashboard for review

### 4. Monitoring

Alert on:
- High denial rates
- Repeated injection attempts
- Unusual tool usage patterns
- Token expiration issues

## License

MIT

## Related

- [MCP Specification](https://modelcontextprotocol.io/)
- [OWASP LLM Top 10](https://owasp.org/www-project-top-10-for-large-language-model-applications/)
- [Capability-Based Security](https://en.wikipedia.org/wiki/Capability-based_security)
