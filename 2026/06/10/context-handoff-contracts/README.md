# Context Handoff Contracts

A TypeScript + Zod implementation of contract-based context handoff between agents. Prevents multi-agent context explosion by passing typed, scoped payloads instead of full transcripts.

## Overview

This code accompanies the article *"Context Handoff Contracts: A Practical Pattern for Preventing Multi-Agent Context Explosion"* (Jun 10, 2026).

It demonstrates:

- **Typed handoff schema** (`src/schema.ts`) — Zod models for `HandoffContract`, `Fact`, `SourceProvenance`, and `SessionEvent`
- **Context compiler** (`src/context-compiler.ts`) — Converts raw session events into a minimal handoff contract, filtering out brainstorming notes, stale tool results, and sensitive decisions
- **Contract validator** (`src/validator.ts`) — Pre-handoff checks: required fields, source provenance, token budget, tool permission alignment, expiry
- **Unit tests** (`tests/contract.test.ts`) — Prove sensitive events are excluded, stale facts are rejected, and the compile → validate pipeline works end to end

## Quick Start

```bash
# Install dependencies
npm install

# Run tests
npm test
```

## Project Structure

```
.
├── src/
│   ├── schema.ts             # Zod schemas for HandoffContract, Fact, SessionEvent
│   ├── context-compiler.ts   # Compiles session events into a HandoffContract
│   └── validator.ts          # Validates a contract before handoff
├── tests/
│   └── contract.test.ts      # Unit tests for schema, compiler, validator, and integration
├── package.json
├── tsconfig.json
├── jest.config.js
└── README.md
```

## Key Concepts

### HandoffContract

A typed payload containing only what the receiving agent needs:

| Field | Description |
|-------|-------------|
| `handoffId` | Unique traceable ID for this handoff |
| `receivingAgent` | Target agent name |
| `task` | Precise task (max 500 chars) |
| `facts` | Array of factual claims with source provenance |
| `excludedContext` | Labels for what was deliberately not passed |
| `allowedTools` | Tools the agent may call |
| `forbiddenTools` | Tools the agent must not call |
| `outputSchema` | Expected output shape reference |
| `expiresAfterMinutes` | Contract validity window |
| `traceId` | Observability correlation ID |

### Context Compiler

The `compileHandoffContract()` function:

1. Filters out events marked `excludeFromHandoff` or matching excluded types
2. Rejects stale tool results (older than `maxResultAgeMinutes`)
3. Extracts facts from tool results (confidence: high), LLM responses (confidence: medium), and user messages (confidence: unverified)
4. Sets provenance metadata (source system, timestamp, method) on every fact
5. Collects excluded-context labels for audit

### Validator

The `validateContract()` function checks before handoff:

- Required fields present
- Sources attached to every fact
- No tool appears in both `allowedTools` and `forbiddenTools`
- Token budget not exceeded (rough estimate)
- Output schema provided if required
- Contract not expired

## Testing

```bash
# Run all tests with verbose output
npm test

# Expected output:
# PASS tests/contract.test.ts
#   HandoffContract schema
#     ✓ accepts a valid contract
#     ✓ rejects a contract missing required fields
#   Context Compiler
#     ✓ excludes events marked excludeFromHandoff
#     ✓ excludes events by type
#     ✓ rejects stale tool results
#     ✓ marks excluded context labels correctly
#     ✓ extracts facts from tool results and LLM responses
#   Validator
#     ✓ passes a valid contract
#     ✓ catches missing traceId
#     ✓ catches facts missing source provenance
#     ✓ catches tools in both allowed and forbidden
#   Integration
#     ✓ compiles from mixed events and validates
```

## Article

See the full article at the [Appropri8 blog](https://appropri8.com/blog/2026/06/10/context-handoff-contracts/) for the pattern description, architecture, and failure modes.
