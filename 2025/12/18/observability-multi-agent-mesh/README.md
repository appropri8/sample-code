# Observability for Multi-Agent Mesh: Traces, Budgets, and "Who Said What"

Complete executable code samples demonstrating observability patterns for multi-agent mesh systems. This repository includes implementations for distributed tracing, budget management, structured event logging, tool output sanitization, and output verification.

## Overview

This repository contains working examples of:

- **OpenTelemetry Instrumentation**: Distributed tracing for agent steps and tool calls
- **Structured Event Logging**: AgentEvent schema with trace_id, span_id, task_id correlation
- **Budget Management**: Token/time/tool call budgets with enforced stop conditions
- **Tool Output Sanitization**: Security and data hygiene for tool outputs
- **Output Verification**: Schema validation and citation checking

## Architecture

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   Agent A   │ ───────>│ Observability│ ───────>│   Tool X    │
│             │         │     Hub      │         │             │
└─────────────┘         │              │         └─────────────┘
                        │ - Traces     │
┌─────────────┐         │ - Budgets    │         ┌─────────────┐
│   Agent B   │ ───────>│ - Events     │ ───────>│   Tool Y    │
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
# Example 1: OpenTelemetry tracing
npm run example:tracing

# Example 2: Structured event logging
npm run example:events

# Example 3: Budget management
npm run example:budget

# Example 4: Tool output sanitization
npm run example:sanitization

# Example 5: Output verification
npm run example:verification
```

## Repository Structure

```
.
├── README.md
├── package.json
├── tsconfig.json
├── src/
│   ├── tracing/
│   │   └── instrumented-agent-executor.ts    # OpenTelemetry instrumentation
│   ├── events/
│   │   └── agent-event-logger.ts              # Structured event logging
│   ├── budget/
│   │   └── budget-manager.ts                  # Budget enforcement
│   ├── sanitization/
│   │   └── tool-output-sanitizer.ts           # Tool output sanitization
│   ├── verification/
│   │   └── output-verifier.ts                 # Output verification
│   └── examples/
│       ├── tracing-example.ts
│       ├── events-example.ts
│       ├── budget-example.ts
│       ├── sanitization-example.ts
│       └── verification-example.ts
└── dist/                                      # Compiled JavaScript (generated)
```

## Key Concepts

### 1. Traceability: End-to-End Spans

OpenTelemetry spans track every agent step and tool call:

- **trace_id**: Same for entire request across all agents
- **span_id**: Unique per operation (agent step or tool call)
- **parent_span_id**: Links spans in delegation chains

This enables you to see the full path from start to finish, find root causes, and understand the flow.

### 2. Controllability: Budgets and Limits

Budget manager enforces limits to prevent runaway costs:

- **Token budgets**: Per-task token limits
- **Time budgets**: Maximum execution time
- **Tool call budgets**: Maximum tool calls per task or tool class
- **Stop conditions**: Max iterations, delegation depth, circular task detection

When limits are exceeded, the system stops immediately.

### 3. Auditability: "Who Said What"

Structured event logging captures:

- **AgentStarted**: When an agent begins processing
- **ToolCalled**: When a tool is invoked
- **ToolResult**: Tool output and latency
- **AgentDelegated**: Agent-to-agent delegation
- **AgentCompleted**: Final result with token usage

All events include trace_id, span_id, task_id for correlation.

### 4. Security: Tool Output Sanitization

Tool outputs are sanitized before entering agent context:

- Removes control characters
- Limits length and line count
- Detects prompt injection patterns
- Normalizes whitespace
- Validates structure

### 5. Quality: Output Verification

Output verifier checks:

- **Schema validation**: Output matches expected JSON schema
- **Required fields**: All required fields are present
- **Citation requirements**: Citations are provided and used
- **Length validation**: Output within size limits

## Examples

### Example 1: OpenTelemetry Tracing

```typescript
import { InstrumentedAgentExecutor } from './tracing/instrumented-agent-executor';

const executor = new InstrumentedAgentExecutor();
const result = await executor.executeStep({
  agentId: 'agent-a',
  taskId: 'task-123',
  traceId: 'trace-abc-123',
  input: { query: 'What is the weather?' },
  model: 'gpt-4',
  promptVersion: 'v2.1',
});
```

Creates OpenTelemetry spans for every agent step, tracks latency, token usage, and errors.

### Example 2: Structured Event Logging

```typescript
import { AgentEventLogger, InMemoryEventStore } from './events/agent-event-logger';

const eventStore = new InMemoryEventStore();
const logger = new AgentEventLogger(eventStore);

logger.logAgentStarted('trace-123', 'span-1', 'task-456', 'agent-a', {
  model: 'gpt-4',
  prompt_version: 'v2.1',
  tenant_id: 'tenant-abc',
});

// Query events
const traceEvents = await eventStore.queryByTraceId('trace-123');
```

Emits structured events with trace_id, span_id, task_id for correlation.

### Example 3: Budget Management

```typescript
import { BudgetManager } from './budget/budget-manager';

const budgetManager = new BudgetManager();
budgetManager.createBudget('task-123', {
  maxTokens: 1000,
  maxTimeMs: 5000,
  maxToolCalls: 10,
});

// Check budgets before operations
budgetManager.checkTokenBudget('task-123', 500);
budgetManager.checkToolCallBudget('task-123', 'database-query', 'database');
```

Enforces token, time, and tool call budgets. Throws errors when limits are exceeded.

### Example 4: Tool Output Sanitization

```typescript
import { sanitizeToolOutput, validateToolOutput } from './sanitization/tool-output-sanitizer';

const sanitized = sanitizeToolOutput(toolOutput);
const validation = validateToolOutput(sanitized);

if (!validation.valid) {
  throw new Error(`Invalid tool output: ${validation.errors.join(', ')}`);
}
```

Sanitizes tool outputs, removes dangerous content, validates structure.

### Example 5: Output Verification

```typescript
import { OutputVerifier } from './verification/output-verifier';

const verifier = new OutputVerifier();
const result = verifier.verify(
  agentOutput,
  {
    schema: outputSchema,
    required_fields: ['status', 'data'],
    require_citations: true,
  },
  citations
);

if (!result.valid) {
  throw new Error(`Verification failed: ${result.errors.join(', ')}`);
}
```

Verifies outputs against schemas, required fields, and citations.

## The 3 Pillars of Observability

### 1. Traceability

**What happened?** End-to-end spans across agents and tools.

- OpenTelemetry spans for every operation
- Correlation IDs (trace_id, span_id, task_id)
- Parent-child relationships in delegation chains

### 2. Controllability

**Can I stop it?** Budgets, rate limits, kill switches.

- Token budgets per task
- Time budgets per delegation chain
- Tool call budgets (max calls / tool classes)
- Stop conditions for loops and flapping

### 3. Auditability

**Who said what?** "Who did what and why" with source tracking.

- Structured event logging
- Citation/grounding signals for tool outputs
- Metadata: model, prompt version, tenant, latency, token usage

## Production Considerations

### OpenTelemetry Backend

In production, configure an OpenTelemetry backend:

- **Jaeger**: For distributed tracing
- **Tempo**: Grafana's tracing backend
- **Datadog/New Relic**: Commercial APM solutions

### Event Store

Replace `InMemoryEventStore` with:

- **Elasticsearch**: For log aggregation and search
- **ClickHouse**: For time-series event data
- **CloudWatch/Cloud Logging**: Managed log services

### Budget Persistence

In production, persist budgets to:

- **Redis**: For fast in-memory budget tracking
- **Database**: For persistent budget storage
- **Distributed cache**: For multi-instance deployments

## Failure Modes Addressed

1. **Delegation chains hide root causes**: Tracing shows the full path
2. **Partial failures look like success**: Event logging captures all steps
3. **One agent's bad context contaminates others**: Sanitization and verification prevent bad data
4. **Runaway costs**: Budgets enforce limits and stop runaway tasks
5. **Prompt injection**: Sanitization detects and removes injection patterns
6. **Wrong outputs**: Verification checks schemas and citations

## Best Practices

1. **Start with tracing**: Add OpenTelemetry spans early
2. **Set budgets early**: Define token and time budgets from the start
3. **Log everything**: Emit structured events for all operations
4. **Sanitize tool outputs**: Always sanitize before entering agent context
5. **Verify outputs**: Use verifiers for critical agent outputs
6. **Monitor proactively**: Build dashboards for failure rates, costs, latency

## Related Article

This code accompanies the article: "Observability for a Multi-Agent Mesh: Traces, Budgets, and 'Who Said What' in Production"

## License

MIT
