# Self-Healing SaaS Provisioning with Reconciliation Loops

This repository contains a production-oriented reference implementation of the reconciliation-loop pattern for SaaS tenant provisioning.

## What is this?

A retry queue asks "did the previous command finish?" A reconciler asks "does the system currently match what the user requested?" This codebase implements the second approach using patterns borrowed from Kubernetes controllers.

## Structure

```
src/
  app.ts                      # Entry point: reconciliation loop + drift scanner
  models/tenant.ts            # TenantSpec, TenantStatus, ReconcileOutcome
  db/
    schema.sql                # PostgreSQL schema
    migrations/
      001_initial_schema.sql  # Initial migration (idempotent)
    client.ts                 # TenantRepository with optimistic concurrency
  providers/
    interfaces.ts             # ProvisioningAction, ProviderAdapter
    identity-provider.ts      # Mock identity provider
    billing-provider.ts       # Mock billing provider
    database-provider.ts      # Mock database provider
    dns-provider.ts           # Realistic HTTP DNS provider adapter
    factory.ts                # Provider factory
  reconciler/
    errors.ts                 # RetryableError, TerminalError
    backoff.ts                # Exponential backoff with jitter
    lock.ts                   # Per-tenant concurrency lock
    planner.ts                # Gap analysis for provisioning/deletion
    executor.ts               # Idempotency-aware action execution
    reconcileTenant.ts        # Core reconciliation algorithm
    scheduler.ts              # Periodic reconciliation scheduler
    drift-scanner.ts          # Detects and repairs external drift
  utils/
    idempotency.ts            # Idempotency key generation
    logging.ts                # Structured logging
    circuit-breaker.ts        # Per-tenant circuit breaker

tests/
  reconciler.test.ts          # Core reconciliation behaviors
  drift-scanner.test.ts       # Drift detection and repair
  idempotency.test.ts         # Key generation and backoff
```

## Running

```bash
npm install
npm run build
npm test
```

You will need a PostgreSQL database. Set `DATABASE_URL` for the app, or `TEST_DATABASE_URL` for tests.

```bash
# Apply schema
psql $DATABASE_URL -f src/db/schema.sql

# Start reconciler
DATABASE_URL=postgres://localhost:5432/reconciliation_provisioning npm start
```

## Key Patterns

- **Desired state is durable.** Spec and status live in PostgreSQL.
- **Each reconciliation cycle does bounded work.** One external call, then exit.
- **Idempotency keys protect against duplicates.** The key is deterministic: `tenantId:generation:actionType`.
- **Optimistic concurrency prevents stale overwrites.** `tryUpdateStatus` checks `desired_generation` before writing.
- **Circuit breakers halt infinite loops.** Five consecutive terminal failures triggers a cooldown.
- **Periodic drift scanner catches external changes.** Deleted resources are recreated with the same idempotency key.

## Test Coverage

1. Reconciliation runs twice without duplicating resources
2. Worker crash recovery: partial progress is preserved and resumed
3. Stale generation cannot overwrite newer status
4. Deleted external resources are recreated by the drift scanner
5. Terminal configuration errors stop retrying after threshold hits
6. Circuit breaker activates after repeated failures
7. Two workers cannot provision the same tenant concurrently

## License

MIT