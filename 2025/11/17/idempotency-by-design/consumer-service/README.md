# Consumer Service with Inbox Pattern

Go-based Kafka consumer that implements the inbox pattern for message deduplication.

## Features

- Inbox pattern for message deduplication
- Outbox processor for publishing messages
- PostgreSQL integration
- Kafka consumer with error handling

## Setup

1. Install dependencies:
```bash
go mod download
```

2. Set environment variables:
```bash
export DATABASE_URL="postgres://localhost/idempotency_example?sslmode=disable"
export KAFKA_BROKERS="localhost:9092"
export KAFKA_TOPIC="order.created"
export OUTBOX_TOPIC="order.created"
```

3. Run migrations (see migrations directory)

4. Run the consumer:
```bash
go run main.go
```

## How It Works

1. Consumer receives message from Kafka
2. Checks inbox table for message_id
3. If exists, skips (already processed)
4. If not, processes message
5. Inserts into inbox table
6. Acknowledges message

The inbox table has a unique constraint on message_id, preventing duplicates even in race conditions.

