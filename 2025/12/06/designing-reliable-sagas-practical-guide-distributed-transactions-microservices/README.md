# Designing Reliable Sagas: A Practical Guide

Complete executable code samples demonstrating saga patterns for handling distributed transactions in microservices.

## Overview

This repository contains TypeScript/Node.js implementations of saga patterns:

- **Saga Orchestrator**: Central coordinator for orchestrating saga workflows
- **Service Handlers**: Example services (Inventory, Payment, Order) that participate in sagas
- **Compensation Logic**: Automatic rollback when steps fail
- **Idempotency**: Handling duplicate messages safely
- **Event-Driven Architecture**: Using Kafka for async messaging

## Architecture

```
┌─────────────────┐
│  API Gateway    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌──────────────┐
│ Saga Orchestrator│────▶│   Kafka      │
└────────┬────────┘     └──────┬───────┘
         │                     │
         ▼                     ▼
┌─────────────────┐     ┌──────────────┐
│  PostgreSQL     │     │   Services   │
│  (Saga State)   │     │  (Order,     │
└─────────────────┘     │   Payment,   │
                        │   Inventory) │
                        └──────────────┘
```

## Prerequisites

- Node.js 18+ installed
- PostgreSQL 13+ running
- Kafka running (or use Docker Compose)
- npm installed

## Installation

```bash
npm install
```

## Database Setup

Create a PostgreSQL database:

```bash
createdb saga_db
```

Or use Docker:

```bash
docker run -d \
  --name postgres-saga \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=saga_db \
  -p 5432:5432 \
  postgres:13
```

## Kafka Setup

Using Docker Compose:

```yaml
version: '3.8'
services:
  zookeeper:
    image: confluentinc/cp-zookeeper:latest
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
  kafka:
    image: confluentinc/cp-kafka:latest
    depends_on:
      - zookeeper
    ports:
      - "9092:9092"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9092
```

Or use a managed Kafka service.

## Configuration

Set environment variables:

```bash
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=saga_db
export DB_USER=postgres
export DB_PASSWORD=postgres
export KAFKA_BROKERS=localhost:9092
export PORT=3000
```

## Running Examples

### 1. Full Saga Orchestrator

Run the complete orchestrator with all services:

```bash
npm run dev
```

This starts:
- Saga orchestrator
- Inventory service
- Payment service
- Order service
- HTTP API server

### 2. Orchestrator Example

Run just the orchestrator:

```bash
npm run example:orchestrator
```

### 3. Service Example

Run a single service (Inventory):

```bash
npm run example:service
```

### 4. Compensation Example

Demonstrates compensation handling:

```bash
npm run example:compensation
```

## API Endpoints

### Start a Saga

```bash
curl -X POST http://localhost:3000/api/orders \
  -H "Content-Type: application/json" \
  -d '{
    "productId": "prod-1",
    "quantity": 2,
    "customerId": "cust-1",
    "total": 100.00
  }'
```

Response:
```json
{
  "success": true,
  "sagaId": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Order saga started"
}
```

### Get Saga State

```bash
curl http://localhost:3000/api/sagas/{sagaId}
```

Response:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "state": "COMPLETED",
  "type": "OrderCheckout",
  "steps": [
    {
      "stepName": "ReserveInventory",
      "sequence": 1,
      "status": "COMPLETED",
      "completedAt": "2025-12-06T10:00:00Z"
    },
    {
      "stepName": "ChargePayment",
      "sequence": 2,
      "status": "COMPLETED",
      "completedAt": "2025-12-06T10:00:01Z"
    },
    {
      "stepName": "ConfirmOrder",
      "sequence": 3,
      "status": "COMPLETED",
      "completedAt": "2025-12-06T10:00:02Z"
    }
  ]
}
```

### Health Check

```bash
curl http://localhost:3000/health
```

## Code Structure

```
src/
  ├── types.ts                 # TypeScript types and interfaces
  ├── utils.ts                 # Utility functions
  ├── database.ts              # Database initialization and seeding
  ├── saga-orchestrator.ts     # Main orchestrator implementation
  ├── inventory-service.ts     # Inventory service handler
  ├── payment-service.ts       # Payment service handler
  ├── order-service.ts         # Order service handler
  └── index.ts                 # Main server with HTTP API

examples/
  ├── orchestrator-example.ts  # Standalone orchestrator example
  ├── service-example.ts       # Standalone service example
  └── compensation-example.ts  # Compensation handling example
```

## Key Patterns

### 1. Saga Orchestration

The orchestrator coordinates the workflow:
- Tracks saga state
- Publishes commands to services
- Handles events and failures
- Triggers compensations

### 2. Idempotency

Every command includes an idempotency key:
```typescript
{
  sagaId: "saga-123",
  stepSequence: 1,
  idempotencyKey: "saga-123-1",
  command: "ReserveInventory",
  payload: { ... }
}
```

Services check the key before processing to prevent duplicates.

### 3. Compensation

When a step fails, compensations run in reverse order:
- If payment fails after inventory is reserved → release inventory
- If order confirmation fails after payment → refund payment and release inventory

### 4. Event-Driven

Services communicate via Kafka topics:
- Commands: `reserveinventory.commands`, `chargepayment.commands`, etc.
- Events: `saga.events` (success), `saga.failures` (failures)
- Compensations: `saga.compensations`

## Testing

### Unit Tests

Test individual components:

```bash
npm test
```

### Integration Tests

Test the full flow:

1. Start PostgreSQL and Kafka
2. Run `npm run dev`
3. Start a saga via API
4. Monitor saga state
5. Verify compensations on failure

### Chaos Testing

Simulate failures:

1. Kill a service mid-execution
2. Drop Kafka messages
3. Delay service responses
4. Verify compensations trigger correctly

## Best Practices

1. **Always use idempotency keys** - Prevent duplicate processing
2. **Design compensations carefully** - Some operations can't be undone
3. **Use async messaging** - Don't use synchronous REST for saga steps
4. **Track saga state** - Store state in a database for recovery
5. **Handle timeouts** - Set timeouts for each step
6. **Monitor and alert** - Track saga success/failure rates
7. **Use correlation IDs** - Include sagaId in all logs and traces

## Common Issues

### Saga Stuck in PENDING

- Check if services are running
- Verify Kafka connectivity
- Check service logs for errors

### Compensations Not Running

- Verify failure events are published
- Check orchestrator is listening to failure topic
- Ensure compensation logic is correct

### Duplicate Processing

- Verify idempotency keys are unique
- Check service idempotency logic
- Ensure processed keys are persisted

## Next Steps

- Add distributed tracing (OpenTelemetry)
- Add metrics and monitoring
- Implement saga inspector UI
- Add retry logic with exponential backoff
- Implement dead letter queue handling
- Add saga timeout handling

## License

MIT

## Resources

- [Saga Pattern - microservices.io](https://microservices.io/patterns/data/saga.html)
- [Distributed Transactions - Martin Kleppmann](https://martin.kleppmann.com/2015/09/26/transactions-at-scale.html)
- [Event-Driven Architecture](https://www.oreilly.com/library/view/designing-event-driven-systems/9781492038252/)

