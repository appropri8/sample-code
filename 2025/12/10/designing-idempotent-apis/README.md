# Designing Idempotent APIs: Complete Code Samples

Complete executable code samples demonstrating idempotent API design patterns for reliable user actions.

## Overview

This repository contains production-ready implementations of idempotent APIs:

- **HTTP API handlers** with idempotency middleware
- **Database storage** using PostgreSQL with unique constraints
- **Redis storage** for low-latency idempotency checks
- **Queue consumers** with idempotent message processing
- **End-to-end examples** showing complete flows

## Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ POST /api/orders
       │ Idempotency-Key: create-order-user123-cart456
       ▼
┌─────────────┐
│ API Gateway │
│ (Middleware)│
└──────┬──────┘
       │
       ▼
┌─────────────┐     ┌──────────────┐
│ Idempotency │────▶│  PostgreSQL  │
│   Store     │     │  or Redis    │
└──────┬──────┘     └──────────────┘
       │
       ▼
┌─────────────┐
│   Service   │
│  (Orders)   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Database   │
└─────────────┘
```

## Prerequisites

- Node.js 18+ installed
- PostgreSQL 13+ running (or Docker)
- Redis running (optional, for Redis examples)
- npm installed

## Installation

```bash
npm install
```

## Database Setup

### Using PostgreSQL

Create database and run schema:

```bash
# Set environment variables
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=idempotency_db
export DB_USER=postgres
export DB_PASSWORD=postgres

# Run setup script
./scripts/setup-db.sh
```

Or manually:

```bash
createdb idempotency_db
psql idempotency_db < src/database.ts  # Extract SQL from IDEMPOTENCY_SCHEMA
```

### Using Docker

```bash
docker run -d \
  --name postgres-idempotency \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=idempotency_db \
  -p 5432:5432 \
  postgres:13

# Then run setup script
./scripts/setup-db.sh
```

## Quick Start

### 1. Start the Server

```bash
npm run dev
```

The server will start on `http://localhost:3000`

### 2. Create an Order (First Request)

```bash
curl -X POST http://localhost:3000/api/orders \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: create-order-user123-cart456-20251210" \
  -d '{
    "user_id": "user123",
    "cart_id": "cart456",
    "items": [
      {"product_id": "prod1", "quantity": 2, "price": 10.00},
      {"product_id": "prod2", "quantity": 1, "price": 5.00}
    ]
  }'
```

Response:
```json
{
  "order_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "user123",
  "cart_id": "cart456",
  "status": "pending",
  "total_amount": 25.00,
  "items": [...],
  "created_at": "2025-12-10T10:00:00Z"
}
```

### 3. Retry with Same Key (Idempotent)

```bash
# Same request, same idempotency key
curl -X POST http://localhost:3000/api/orders \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: create-order-user123-cart456-20251210" \
  -d '{
    "user_id": "user123",
    "cart_id": "cart456",
    "items": [
      {"product_id": "prod1", "quantity": 2, "price": 10.00},
      {"product_id": "prod2", "quantity": 1, "price": 5.00}
    ]
  }'
```

Response (same order, no duplicate):
```json
{
  "order_id": "550e8400-e29b-41d4-a716-446655440000",
  ...
}
```

## Repository Structure

```
.
├── README.md
├── package.json
├── tsconfig.json
├── src/
│   ├── index.ts                    # Main Express server
│   ├── database.ts                 # PostgreSQL idempotency store
│   ├── redis-store.ts              # Redis idempotency store
│   ├── idempotency-middleware.ts   # Express middleware
│   ├── order-service.ts            # Order service with idempotency
│   ├── queue-consumer.ts           # Kafka consumer with idempotency
│   ├── types.ts                    # TypeScript types
│   └── utils.ts                    # Utility functions
├── examples/
│   ├── basic-handler.ts            # Simple handler example
│   ├── redis-handler.ts            # Redis-based handler
│   └── queue-consumer-example.ts   # Queue consumer example
└── scripts/
    └── setup-db.sh                  # Database setup script
```

## Key Components

### Idempotency Middleware

The middleware (`src/idempotency-middleware.ts`) handles:
- Extracting `Idempotency-Key` header
- Checking idempotency store for existing keys
- Returning cached responses for completed requests
- Creating processing records
- Updating records with responses

### Database Store

The PostgreSQL store (`src/database.ts`) provides:
- Atomic key creation (unique constraint prevents race conditions)
- Response caching
- TTL-based expiration
- Status tracking (processing, completed, failed)

### Redis Store

The Redis store (`src/redis-store.ts`) provides:
- Low-latency lookups (sub-millisecond)
- Built-in TTL
- Atomic check-and-set operations
- High throughput

### Queue Consumer

The queue consumer (`src/queue-consumer.ts`) shows:
- Processing Kafka messages idempotently
- Tracking processed messages in database
- Handling duplicate deliveries
- Graceful error handling

## Usage Examples

### Basic HTTP Handler

See `examples/basic-handler.ts` for a simple Express handler with idempotency.

### Redis-Based Handler

See `examples/redis-handler.ts` for using Redis instead of PostgreSQL for lower latency.

### Queue Consumer

See `examples/queue-consumer-example.ts` for processing messages from Kafka with idempotency.

## Testing Idempotency

### Test Retry Behavior

```bash
# First request
curl -X POST http://localhost:3000/api/orders \
  -H "Idempotency-Key: test-key-123" \
  -d '{"user_id": "user1", "cart_id": "cart1", "items": []}'

# Retry with same key (should return same order)
curl -X POST http://localhost:3000/api/orders \
  -H "Idempotency-Key: test-key-123" \
  -d '{"user_id": "user1", "cart_id": "cart1", "items": []}'
```

### Test Key Reuse Detection

```bash
# First request
curl -X POST http://localhost:3000/api/orders \
  -H "Idempotency-Key: test-key-456" \
  -d '{"user_id": "user1", "cart_id": "cart1", "items": []}'

# Reuse key with different request (should fail)
curl -X POST http://localhost:3000/api/orders \
  -H "Idempotency-Key: test-key-456" \
  -d '{"user_id": "user2", "cart_id": "cart2", "items": []}'
```

Expected response:
```json
{
  "error": "Idempotency key reused with different request",
  "code": "IDEMPOTENCY_KEY_REUSED"
}
```

## Configuration

Set environment variables:

```bash
# Database
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=idempotency_db
export DB_USER=postgres
export DB_PASSWORD=postgres

# Redis (optional)
export REDIS_URL=redis://localhost:6379

# Kafka (for queue examples)
export KAFKA_BROKERS=localhost:9092

# Server
export PORT=3000
```

## Cleanup

Clean up expired idempotency keys:

```bash
curl -X POST http://localhost:3000/api/admin/cleanup
```

Or run cleanup job periodically:

```bash
# Add to cron
0 2 * * * curl -X POST http://localhost:3000/api/admin/cleanup
```

## Best Practices

1. **Generate keys on client side**: Clients know what action they're performing
2. **Include user context**: Scope keys to users to prevent collisions
3. **Set reasonable TTLs**: 24 hours is usually enough
4. **Hash request bodies**: Detect key reuse with different requests
5. **Use transactions**: Ensure atomicity when creating records
6. **Monitor cache hit rates**: Track how many retries are served from cache
7. **Clean up expired keys**: Prevent storage growth

## Common Issues

### "Idempotency key already exists" on first request

This means another request with the same key is already processing. This is expected behavior - return 409 Conflict.

### Duplicate orders still created

Check that:
- Idempotency key is being sent correctly
- Database has unique constraint on `idempotency_key` in orders table
- Service checks for existing orders before creating

### High latency on idempotency checks

Consider using Redis for hot keys (recent requests) and PostgreSQL for audit trail.

## Next Steps

- Add monitoring and alerting
- Implement multi-region idempotency
- Add request/response compression for large payloads
- Implement idempotency key generation helpers for clients
- Add integration tests with chaos scenarios

## Resources

- [Idempotency in REST APIs](https://restfulapi.net/idempotent-rest-apis/)
- [Stripe Idempotency Keys](https://stripe.com/docs/api/idempotent_requests)
- [AWS API Gateway Idempotency](https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-idempotency.html)

## License

MIT

## Author

Yusuf Elborey
