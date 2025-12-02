# Designing Backpressure-First Systems

Complete executable code samples demonstrating backpressure patterns for building resilient systems that handle traffic spikes gracefully.

## Overview

This repository contains TypeScript/Node.js implementations of key backpressure patterns:

- **Rate Limiters**: Token bucket and leaky bucket algorithms
- **Bounded Queues**: Queues with maximum size limits
- **Worker Pools**: Fixed concurrency worker pools with bounded job queues
- **Circuit Breakers**: Protection against failing dependencies
- **Concurrency Limiters**: Limiting concurrent operations
- **Request Context**: Timeout and cancellation propagation

## Installation

```bash
npm install
```

## Build

```bash
npm run build
```

## Running Examples

### Rate Limiter Example

```bash
npm run dev -- examples/rate-limiter-example.ts
```

Demonstrates:
- Token bucket rate limiting
- Leaky bucket rate limiting
- Per-client rate limiting

### Circuit Breaker Example

```bash
npm run dev -- examples/circuit-breaker-example.ts
```

Demonstrates:
- Circuit breaker state transitions (CLOSED → OPEN → HALF_OPEN)
- Failure threshold handling
- Automatic recovery

### Worker Pool Example

```bash
npm run dev -- examples/worker-pool-example.ts
```

Demonstrates:
- Bounded worker pool
- Job queue management
- Queue full handling

### Request Context Example

```bash
npm run dev -- examples/request-context-example.ts
```

Demonstrates:
- Request deadline tracking
- Timeout propagation
- AbortSignal integration

## Running the Full Server

The main server demonstrates all patterns working together:

```bash
npm run dev
```

The server exposes:

- `POST /api/orders` - Order endpoint with full backpressure
- `GET /api/metrics` - Metrics endpoint showing system state
- `GET /health` - Health check endpoint

### Example Request

```bash
curl -X POST http://localhost:3000/api/orders \
  -H "Content-Type: application/json" \
  -H "X-User-Id: user-123" \
  -d '{"orderId": "order-1", "amount": 100}'
```

### Example Response (Rate Limited)

```json
{
  "error": "Rate limit exceeded",
  "retryAfter": 2
}
```

HTTP Status: 429
Header: `Retry-After: 2`

### Example Response (Service Overloaded)

```json
{
  "error": "Service overloaded",
  "retryAfter": 10
}
```

HTTP Status: 503
Header: `Retry-After: 10`

### Example Response (Success)

```json
{
  "message": "Order queued",
  "orderId": "order-1",
  "queueSize": 5
}
```

HTTP Status: 202

## Code Structure

```
src/
  ├── rate-limiter.ts          # Token bucket, leaky bucket, per-client limiter
  ├── bounded-queue.ts         # Bounded queue and priority queue
  ├── worker-pool.ts           # Worker pool with bounded queue
  ├── circuit-breaker.ts       # Circuit breaker implementation
  ├── concurrency-limiter.ts  # Concurrency limiting
  ├── request-context.ts       # Request context with timeouts
  └── index.ts                 # Main server demonstrating all patterns

examples/
  ├── rate-limiter-example.ts
  ├── circuit-breaker-example.ts
  ├── worker-pool-example.ts
  └── request-context-example.ts
```

## Key Patterns

### 1. Rate Limiting

**Token Bucket:**
- Smooth rate limiting
- Tokens refill at fixed rate
- Good for API rate limits

**Leaky Bucket:**
- Strict rate limiting
- Fixed leak rate
- Good for strict quotas

### 2. Bounded Queues

- Always set maximum size
- Reject when full (don't grow unbounded)
- Rule of thumb: 2-3x worker capacity

### 3. Worker Pools

- Fixed number of workers
- Bounded job queue
- Process jobs sequentially per worker

### 4. Circuit Breakers

- Stop calling failing dependencies
- Three states: CLOSED, OPEN, HALF_OPEN
- Automatic recovery testing

### 5. Concurrency Limiting

- Limit concurrent operations
- Queue excess operations
- Process when capacity available

### 6. Request Context

- Track request deadlines
- Propagate through call stack
- Enable timeout and cancellation

## Testing

Run the examples to see backpressure in action:

```bash
# Terminal 1: Start server
npm run dev

# Terminal 2: Send requests
for i in {1..20}; do
  curl -X POST http://localhost:3000/api/orders \
    -H "Content-Type: application/json" \
    -H "X-User-Id: user-123" \
    -d "{\"orderId\": \"order-$i\", \"amount\": 100}"
  echo ""
done
```

Watch the server logs to see:
- Rate limiting in action
- Queue filling up
- Circuit breaker state changes
- Request rejections with proper status codes

## Metrics

Check system metrics:

```bash
curl http://localhost:3000/api/metrics
```

Response:
```json
{
  "queueSize": 5,
  "queueFull": false,
  "activeConcurrency": 3,
  "queuedConcurrency": 2,
  "circuitBreakerState": "CLOSED",
  "circuitBreakerFailures": 0
}
```

## Best Practices

1. **Always bound your queues** - Unbounded queues lead to memory exhaustion
2. **Set timeouts everywhere** - Don't let operations hang forever
3. **Use circuit breakers for external calls** - Fail fast when dependencies are down
4. **Rate limit at the edge** - Reject excess requests early
5. **Monitor queue depth** - Alert when queues grow
6. **Respect Retry-After headers** - Don't retry immediately
7. **Use priority queues** - Drop low-priority work first when overloaded

## License

MIT

