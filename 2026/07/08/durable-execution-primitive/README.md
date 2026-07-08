# Durable Execution as a System Design Primitive

Reference code for the article **"Stop Building Retry Glue: Design Long-Running Workflows with Durable Execution"** (July 8, 2026).

## What this demonstrates

A side-by-side comparison of a naive order service and a durable workflow for the same order fulfillment flow.

## Project layout

```
.
├── src/
│   ├── index.ts              # public exports
│   ├── naive.ts              # naive service with manual status columns and try/catch
│   ├── activities.ts         # idempotent payment, inventory, shipping, notification providers
│   ├── engine.ts             # in-memory workflow engine with history/replay
│   └── workflow.ts           # durable order fulfillment workflow definition
├── tests/
│   └── recovery.test.ts      # prove crash-after-payment recovery without double-charge
├── package.json
├── tsconfig.json
├── jest.config.ts
└── README.md
```

## Key concepts

### Naive approach (`src/naive.ts`)

The naive service manages business state inside a single try/catch block with mutable status columns. If the worker crashes after `charge()` but before `reserve()`, you restart from zero and charge again.

### Durable approach (`src/workflow.ts` + `src/engine.ts`)

The durable approach separates workflow logic from side effects. The `Engine` records each step in a history store. When the workflow is resumed, completed steps are skipped. Retried steps use idempotency keys so external calls happen at most once.

### Idempotency keys (`src/activities.ts`)

Every external call receives a stable key (`payment:charge:${orderId}`). The registry tracks results by key. If the engine retries the activity, the registry returns the cached result instead of calling the provider again.

## Running

```bash
npm install
npm test
```

## Failure scenarios covered in tests

1. Worker crashes after payment succeeds. Resume skips the charge and continues with inventory.
2. Shipment times out. Fix the provider and resume; completed steps are not re-executed.

## Article

Read the full article at [appropri8.com/blog/2026/07/08/durable-execution-primitive/](https://appropri8.com/blog/2026/07/08/durable-execution-primitive/).
