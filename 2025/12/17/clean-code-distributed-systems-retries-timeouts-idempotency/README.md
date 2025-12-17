# Clean Code for Distributed Systems: Retries, Timeouts, and Idempotency

Complete executable code samples demonstrating clean code patterns for reliability in distributed systems.

## Overview

This repository contains before/after examples showing how to structure reliability code (retries, timeouts, idempotency) in a clean, readable way:

- **Before examples**: Messy code with reliability logic mixed with business logic
- **After examples**: Clean code with reliability separated and made explicit
- **Resilience library**: Three clean primitives (timeout, retry, idempotency)

## Architecture

```
┌─────────────────────────────────────┐
│   Business Logic (Pure Functions)   │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│   Resilience Primitives            │
│   - callWithTimeout                 │
│   - retry                           │
│   - ensureIdempotent                │
└─────────────────────────────────────┘
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
# Example A: HTTP call with retries and timeouts
npm run example:http

# Example B: Message handler with idempotency
npm run example:message
```

### 3. Run Tests

```bash
npm test
```

## Repository Structure

```
.
├── README.md
├── package.json
├── tsconfig.json
├── src/
│   ├── resilience/                  # Resilience primitives
│   │   ├── timeout.ts               # Timeout wrapper
│   │   ├── retry.ts                 # Retry wrapper with explicit rules
│   │   ├── idempotency.ts           # Idempotency wrapper
│   │   └── index.ts                 # Exports
│   ├── before/                      # Messy examples
│   │   ├── payment-service.ts       # Before: retry/timeout mixed in
│   │   └── order-handler.ts         # Before: idempotency mixed in
│   ├── after/                       # Clean examples
│   │   ├── payment-service.ts       # After: clean HTTP call pattern
│   │   └── order-handler.ts         # After: clean message handler pattern
│   ├── examples/                     # Runnable examples
│   │   ├── http-call-example.ts     # HTTP call example
│   │   └── message-handler-example.ts # Message handler example
│   └── types.ts                     # Shared type definitions
└── tests/                           # Test files
```

## Key Concepts

### 1. Reliability at Boundaries

Reliability code belongs at system boundaries (HTTP calls, database calls, queue operations), not mixed with business logic.

### 2. Explicit Policies

Define retry/timeout policies in one place. Make them data, not code scattered everywhere.

### 3. Visible Behavior

When you read a function, you should know:
- Does it retry? How many times?
- Does it timeout? How long?
- Is it idempotent? What's the key?

### 4. Three Clean Primitives

- **callWithTimeout**: Makes timeouts explicit
- **retry**: Makes retry behavior visible with explicit rules
- **ensureIdempotent**: Makes idempotency explicit with a key and store

## Examples

### Example A: HTTP Call

**Before**: Retry and timeout logic mixed with business logic
```typescript
// Hard to see what the function does
async chargeCustomer(amount, customerId) {
  // 50 lines of mixed retry/timeout/business logic
}
```

**After**: Clean separation with explicit policies
```typescript
// Clear: uses payment policy (5s timeout, 3 retries)
async chargeCustomer(amount: number, customerId: string) {
  return await callHttpWithPolicy('payment', () =>
    this.callPaymentApi({ amount, customerId })
  );
}
```

### Example B: Message Handler

**Before**: Idempotency check mixed with business logic
```typescript
// Hard to see idempotency handling
async handleOrderMessage(message) {
  // Validation, idempotency, business logic all mixed
}
```

**After**: Clean step-by-step flow
```typescript
// Clear: validate → ensure idempotency → process → ack
async handleOrderMessage(message: OrderMessage) {
  validateOrderMessage(message);
  
  const order = await ensureIdempotent(
    () => processOrder(message, ...),
    { idempotencyKey: message.messageId, ... }
  );
  
  await this.messageQueue.ack(message.messageId);
  return order;
}
```

## Resilience Primitives

### callWithTimeout

```typescript
const result = await callWithTimeout(
  () => paymentService.charge(amount),
  { timeoutMs: 5000 }
);
```

### retry

```typescript
const result = await retry(
  () => callWithTimeout(() => paymentService.charge(amount), { timeoutMs: 5000 }),
  {
    maxAttempts: 3,
    shouldRetry: (error) => error.statusCode === 503 || error.statusCode === 429,
    backoffMs: 1000
  }
);
```

### ensureIdempotent

```typescript
const order = await ensureIdempotent(
  () => createOrder(userId, items),
  {
    idempotencyKey: `order-${userId}-${Date.now()}`,
    idempotencyStore: redisClient
  }
);
```

## Best Practices

1. **Always use timeouts with retries**: Retries without timeouts can make outages worse
2. **Retry selectively**: Only retry server errors (5xx) and rate limits (429), not client errors (4xx)
3. **Make idempotency explicit**: Always provide a key, a store, and make the rule visible
4. **Log decisions**: Log when you retry, why you retry, when you timeout
5. **Don't log secrets**: Log the shape and timing, not the data

## Testing

The clean patterns make testing easier:

- Test business logic separately (pure functions)
- Test resilience primitives separately (timeout, retry, idempotency)
- Mock dependencies easily (injected, not global)

## Related Article

This code accompanies the article: "Clean Code for Distributed Systems: Make Retries, Timeouts, and Idempotency Readable"

## License

MIT
