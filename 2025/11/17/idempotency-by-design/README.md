# Idempotency by Design: Exactly-Once Effects on At-Least-Once Delivery

Complete working examples demonstrating idempotency patterns in distributed systems.

This repository contains:

1. **HTTP Service** (Node.js + PostgreSQL) - REST API with idempotency keys
2. **Consumer Service** (Go + Kafka) - Message consumer with inbox pattern
3. **SQL Migrations** - Database schema for idempotency, outbox, and inbox
4. **Load Tests** (k6) - Tests for duplicate handling under load

## Quick Start

### Prerequisites

- Node.js 18+
- Go 1.21+
- PostgreSQL 14+
- Kafka (optional, for consumer example)
- k6 (optional, for load testing)

### Setup

1. **Create database:**
```bash
createdb idempotency_example
```

2. **Run migrations:**
```bash
psql idempotency_example < migrations/001_idempotency_keys.sql
psql idempotency_example < migrations/002_orders.sql
psql idempotency_example < migrations/003_outbox.sql
psql idempotency_example < migrations/004_inbox.sql
psql idempotency_example < migrations/005_cleanup_job.sql
```

3. **Start HTTP service:**
```bash
cd http-service
npm install
export DATABASE_URL="postgresql://localhost/idempotency_example"
npm start
```

4. **Test the API:**
```bash
# First request
curl -X POST http://localhost:3000/orders \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: test-key-123" \
  -d '{"userId": "user-1", "amount": 100}'

# Retry with same key (should return same result)
curl -X POST http://localhost:3000/orders \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: test-key-123" \
  -d '{"userId": "user-1", "amount": 100}'
```

5. **Run consumer (requires Kafka):**
```bash
cd consumer-service
go mod download
export DATABASE_URL="postgres://localhost/idempotency_example?sslmode=disable"
export KAFKA_BROKERS="localhost:9092"
export KAFKA_TOPIC="order.created"
go run main.go
```

6. **Run load tests:**
```bash
cd load-test
k6 run test.js
```

## Architecture

### HTTP Service

The HTTP service demonstrates:

- **Idempotency keys** at the API edge
- **Transaction boundaries** for atomicity
- **Status tracking** (processing, completed, failed)
- **Response caching** for duplicate requests
- **Outbox pattern** for reliable message publishing

Key features:
- Validates `Idempotency-Key` header
- Checks for existing results before processing
- Uses `FOR UPDATE` to prevent race conditions
- Stores results for 24 hours (configurable)
- Writes to outbox table atomically with order creation

### Consumer Service

The consumer service demonstrates:

- **Inbox pattern** for message deduplication
- **Unique constraints** to prevent duplicates
- **Race condition handling** for concurrent consumers
- **Outbox processor** for publishing messages

Key features:
- Checks inbox before processing
- Inserts into inbox after processing
- Handles race conditions gracefully
- Processes outbox table periodically

### Database Schema

**idempotency_keys:**
- Stores idempotency keys and cached results
- Tracks status (processing, completed, failed)
- Includes expiration for cleanup

**outbox:**
- Transactional outbox for reliable publishing
- Tracks published status
- Supports retry logic

**inbox:**
- Message deduplication table
- Unique constraint on message_id
- Tracks processing time

**orders:**
- Business domain table
- Created atomically with outbox records

## Patterns Explained

### Idempotency Keys

Clients send a unique key with each request. The server:
1. Checks if key exists
2. If exists and completed, returns cached result
3. If exists and processing, returns 409 Conflict
4. If not exists, processes and stores result

### Outbox Pattern

When you need to:
- Update database
- Publish message

Do both atomically:
1. Write to database and outbox in one transaction
2. Background job reads outbox
3. Publishes to message queue
4. Marks as published

### Inbox Pattern

When consuming messages:
1. Check inbox for message_id
2. If exists, skip (already processed)
3. If not, process message
4. Insert into inbox
5. Acknowledge message

Unique constraint prevents duplicates even in race conditions.

## Testing

### Unit Tests

```bash
# HTTP service
cd http-service
npm test

# Consumer service
cd consumer-service
go test ./...
```

### Integration Tests

```bash
# Test idempotency
./test-idempotency.sh

# Test concurrent duplicates
./test-concurrent.sh
```

### Load Tests

```bash
cd load-test
k6 run test.js
```

The load test:
- Sends requests with idempotency keys
- Retries with same keys
- Tests concurrent duplicates
- Verifies same results are returned

## Production Considerations

### TTL Configuration

Set TTL based on your retry window:
- If clients retry for up to 1 hour, set TTL to 2-3 hours
- Too short: legitimate retries get rejected
- Too long: storage fills up

### Storage Choice

**Redis:**
- Fast, good for high throughput
- Data can be lost (not durable)
- Good for non-critical operations

**Database:**
- Durable, reliable
- Slower than Redis
- Good for critical operations

**Hybrid:**
- Check Redis first
- Fall back to database
- Best of both worlds

### Monitoring

Track:
- Dedupe rate (how often keys are reused)
- Processing time
- Error rates
- Storage usage

Alert on:
- Sudden spike in duplicates
- High duplicate rate for specific operation
- Idempotency check failures

## Limitations

These examples are simplified for clarity:

- No distributed locking (use Redis or database locks in production)
- Simple error handling (add retry logic, circuit breakers)
- Basic logging (add structured logging, tracing)
- In-memory state (use external storage in production)

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
  // Fall back to database
  return await checkIdempotencyDB(key);
}
```

### Add Saga Support

```javascript
const sagaId = crypto.randomUUID();
const orderKey = `${sagaId}:create-order`;
const paymentKey = `${sagaId}:charge-payment`;
// Each step has its own key
```

### Add Observability

```javascript
logger.info('Processing request', {
  idempotencyKey,
  userId,
  operation: 'create_order',
  traceId
});

metrics.increment('idempotency.duplicate', {
  operation: 'create_order'
});
```

## References

- [Idempotency Keys RFC](https://datatracker.ietf.org/doc/html/draft-ietf-httpapi-idempotency-key-header)
- [Transactional Outbox Pattern](https://microservices.io/patterns/data/transactional-outbox.html)
- [Inbox Pattern](https://event-driven.io/en/inbox_pattern_in_event_driven_systems/)

## License

MIT

