# Zero-Downtime Schema Migrations: Expand-Contract Pattern

Complete working examples demonstrating zero-downtime schema migrations using the expand-contract pattern with dual-write cutovers.

This repository contains:

1. **PostgreSQL Migrations** - Safe schema changes (expand, dual-write, contract)
2. **Node.js Service** - REST API with dual-write support
3. **Backfill Worker** - Chunked backfilling with resume tokens
4. **Load Tests** (k6) - Tests for migration under load

## Quick Start

### Prerequisites

- Node.js 18+
- PostgreSQL 14+
- k6 (optional, for load testing)

### Setup

1. **Create database:**
```bash
createdb zero_downtime_migrations
```

2. **Set environment variables:**
```bash
export DATABASE_URL="postgresql://user:password@localhost/zero_downtime_migrations"
```

3. **Run migrations:**
```bash
# Initial schema
psql $DATABASE_URL < migrations/001_initial_schema.sql

# Expand phase: Add nullable status column
psql $DATABASE_URL < migrations/002_expand_add_status.sql

# Backfill progress table
psql $DATABASE_URL < migrations/003_backfill_progress.sql

# Contract phase (only after migration is complete)
# psql $DATABASE_URL < migrations/004_contract_drop_old.sql
```

4. **Install dependencies:**
```bash
npm install
```

5. **Start server:**
```bash
npm start
```

6. **Run backfill:**
```bash
npm run backfill
```

## Architecture

### Phase 1: Expand

Add new columns as nullable (no defaults, no locks):

```sql
ALTER TABLE orders ADD COLUMN status VARCHAR(50);
CREATE INDEX CONCURRENTLY idx_orders_status ON orders(status);
```

### Phase 2: Dual-Write

Write to both old and new schemas:

```javascript
// Enable dual-write
export DUAL_WRITE=true
export WRITE_TO_NEW=true

// Application writes to both
await createOrder({ userId: 1, amount: 100, status: 'pending' });
```

### Phase 3: Contract

Switch reads to new schema, drop old columns:

```sql
-- After migration is complete
ALTER TABLE orders DROP COLUMN old_status;
```

## Usage Examples

### Basic Service

```bash
# Start server
npm start

# Create order
curl -X POST http://localhost:3000/orders \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: test-123" \
  -d '{"userId": 1, "amount": 100, "status": "pending"}'

# Get order
curl http://localhost:3000/orders/1

# Shadow read (compare old vs new)
curl http://localhost:3000/orders/1/shadow
```

### Backfill Worker

```bash
# Run backfill
npm run backfill

# Or with custom config
node examples/backfill.js
```

The backfill worker:
- Processes rows in batches (default: 1000)
- Throttles between batches (default: 100ms)
- Saves resume tokens for recovery
- Tracks metrics (rows/sec, lag)

### Feature Flags

Control migration phases with environment variables:

```bash
# Phase 1: Expand (write to old only)
export WRITE_TO_NEW=false
export READ_FROM_NEW=false

# Phase 2: Dual-write
export DUAL_WRITE=true
export WRITE_TO_NEW=true
export READ_FROM_NEW=false

# Phase 3: Contract (read from new)
export READ_FROM_NEW=true
export WRITE_TO_NEW=true
export DUAL_WRITE=false
```

## Load Testing

Run load tests with k6:

```bash
# Install k6
brew install k6  # macOS
# or
sudo apt-get install k6  # Linux

# Run load test
npm run load-test
```

The load test:
- Ramps up to 100 concurrent users
- Tests order creation and retrieval
- Tests idempotency with retries
- Monitors p95/p99 latency and error rates

## Testing

Run unit tests:

```bash
npm test
```

Tests cover:
- Order creation with different flags
- Dual-write functionality
- Shadow reads
- Backfill worker with resume tokens

## Migration Steps

### Step 1: Expand

1. Add nullable column (no default)
2. Create index concurrently
3. Deploy code that handles both old and new schemas

```sql
ALTER TABLE orders ADD COLUMN status VARCHAR(50);
CREATE INDEX CONCURRENTLY idx_orders_status ON orders(status);
```

### Step 2: Backfill

1. Run backfill worker to populate new column
2. Monitor progress and metrics
3. Verify data consistency

```bash
npm run backfill
```

### Step 3: Dual-Write

1. Enable dual-write flag
2. Write to both old and new schemas
3. Monitor for errors

```bash
export DUAL_WRITE=true
export WRITE_TO_NEW=true
```

### Step 4: Switch Reads

1. Enable read-from-new flag
2. Monitor error rates
3. Run shadow reads to compare

```bash
export READ_FROM_NEW=true
```

### Step 5: Contract

1. Stop writing to old columns
2. Wait a few days
3. Drop old columns

```sql
ALTER TABLE orders DROP COLUMN old_status;
```

## Monitoring

Monitor these metrics during migration:

- **Latency**: p95, p99 request duration
- **Errors**: Error rate (should be < 1%)
- **Backfill**: Rows processed, rows/sec, lag
- **Shadow reads**: Mismatch rate (should be 0%)

Set up alerts for:
- P95 latency > 500ms
- Error rate > 1%
- Backfill lag increasing
- Shadow read mismatches

## Best Practices

1. **Add nullable columns**: No defaults, no locks
2. **Create indexes concurrently**: Avoids table locks
3. **Backfill in chunks**: Process in batches with throttling
4. **Use feature flags**: Gradual rollout with rollback capability
5. **Monitor metrics**: Track latency, errors, and progress
6. **Shadow reads**: Compare old and new schemas
7. **Have rollback plan**: Be ready to revert if needed

## Production Considerations

### TTL and Cleanup

Set TTLs for backfill progress:

```sql
DELETE FROM backfill_progress 
WHERE updated_at < NOW() - INTERVAL '7 days';
```

### Error Handling

- Use retries with exponential backoff
- Log all errors for debugging
- Set up alerts for error spikes

### Rollback Plan

If something goes wrong:

1. Turn off read-from-new flag
2. Turn off write-to-new flag
3. Keep old columns for recovery
4. Investigate and fix issues

## Limitations

These examples are simplified for clarity:

- No distributed locking (use Redis or database locks in production)
- Basic error handling (add retry logic, circuit breakers)
- Simple logging (add structured logging, tracing)
- Single database (extend for read replicas)

## Extending

### Add Redis Support

```javascript
const redis = require('redis');
const client = redis.createClient();

async function checkIdempotency(key) {
  const cached = await client.get(`idempotency:${key}`);
  if (cached) {
    return JSON.parse(cached);
  }
  return null;
}
```

### Add Observability

```javascript
const { metrics } = require('@opentelemetry/api');

metrics.getMeter('orders').createCounter('orders.created', {
  description: 'Number of orders created'
}).add(1);
```

### Add Read Replicas

```javascript
const readPool = new Pool({ connectionString: READ_REPLICA_URL });
const writePool = new Pool({ connectionString: PRIMARY_URL });
```

## References

- [PostgreSQL CREATE INDEX CONCURRENTLY](https://www.postgresql.org/docs/current/sql-createindex.html#SQL-CREATEINDEX-CONCURRENTLY)
- [Zero-Downtime Migrations](https://github.com/github/gh-ost)
- [Expand-Contract Pattern](https://martinfowler.com/bliki/ParallelChange.html)

## License

MIT

