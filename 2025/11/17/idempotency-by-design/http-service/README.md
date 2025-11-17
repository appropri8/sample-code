# HTTP Service with Idempotency Keys

Node.js Express service demonstrating idempotency keys at the API edge.

## Features

- Idempotency key validation
- Response caching for duplicate requests
- Transaction boundaries for atomicity
- Outbox pattern for message publishing
- Status tracking (processing, completed, failed)

## Setup

1. Install dependencies:
```bash
npm install
```

2. Set environment variables:
```bash
export DATABASE_URL="postgresql://localhost/idempotency_example"
export PORT=3000
```

3. Run migrations (see migrations directory)

4. Start server:
```bash
npm start
```

## Usage

### Create Order

```bash
curl -X POST http://localhost:3000/orders \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: unique-key-123" \
  -d '{
    "userId": "user-123",
    "amount": 100.50
  }'
```

### Retry Same Request

```bash
# Same key, same request - returns cached result
curl -X POST http://localhost:3000/orders \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: unique-key-123" \
  -d '{
    "userId": "user-123",
    "amount": 100.50
  }'
```

## Response Codes

- `201 Created` - New order created
- `200 OK` - Cached result returned
- `409 Conflict` - Request already processing
- `400 Bad Request` - Missing idempotency key or invalid request
- `500 Internal Server Error` - Processing error

## How It Works

1. Client sends request with `Idempotency-Key` header
2. Server checks for existing result
3. If found and completed, returns cached result (200)
4. If found and processing, returns 409 Conflict
5. If not found, marks as processing
6. Processes request
7. Stores result
8. Returns result (201)

All within database transactions to ensure atomicity.

