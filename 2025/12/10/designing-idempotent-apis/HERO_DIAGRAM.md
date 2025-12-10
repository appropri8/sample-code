# Hero Diagram: Idempotent API Flow

## Diagram Description

This diagram shows the end-to-end flow of an idempotent API request, from client retry to cached response.

## ASCII Diagram

```
┌─────────────┐
│   Client    │
│  (Browser/  │
│   Mobile)   │
└──────┬──────┘
       │
       │ POST /api/orders
       │ Idempotency-Key: create-order-user123-cart456-20251210
       │
       ▼
┌─────────────────────────────────────┐
│         API Gateway                 │
│  ┌───────────────────────────────┐ │
│  │  Idempotency Middleware       │ │
│  │  1. Extract key from header    │ │
│  │  2. Check idempotency store   │ │
│  │  3. Return cached if exists   │ │
│  └───────────────────────────────┘ │
└──────┬──────────────────────────────┘
       │
       │ Key exists? ──No──┐
       │                   │
       Yes                  │
       │                   │
       ▼                   ▼
┌─────────────┐    ┌──────────────┐
│ Return      │    │ Create       │
│ Cached      │    │ Processing   │
│ Response    │    │ Record       │
└─────────────┘    └──────┬───────┘
                          │
                          ▼
                   ┌──────────────┐
                   │   Forward    │
                   │   to Service │
                   └──────┬───────┘
                          │
                          ▼
                   ┌──────────────┐
                   │ Order Service│
                   │ 1. Check DB  │
                   │ 2. Create    │
                   │    Order     │
                   └──────┬───────┘
                          │
                          ▼
                   ┌──────────────┐
                   │  PostgreSQL  │
                   │  (Orders)    │
                   └──────┬───────┘
                          │
                          ▼
                   ┌──────────────┐
                   │ Update       │
                   │ Idempotency  │
                   │ Record        │
                   │ (completed)  │
                   └──────┬───────┘
                          │
                          ▼
                   ┌──────────────┐
                   │ Return       │
                   │ Response     │
                   └──────────────┘
```

## Timeline Diagram

```
Time    Client              Gateway              Store              Service              DB
─────────────────────────────────────────────────────────────────────────────────────────
0ms     POST /orders
        Idempotency-Key:
        create-order-123
        ────────────────────────────────────────────────────────────────────────────────►
        
50ms                                    Check key
                                        ────────────────────────────────────────────────►
                                        
100ms                                   Key not found
                                        Create processing
                                        record
                                        ────────────────────────────────────────────────►
                                        
150ms                                   Forward request
                                        ────────────────────────────────────────────────►
                                        
200ms                                                           Check existing
                                                                 order
                                                                 ────────────────────────►
                                                                 
250ms                                                           Create order
                                                                 ────────────────────────►
                                                                 
300ms                                                           Order created
                                                                 (order_id: 42)
                                                                 ◄───────────────────────
                                                                 
350ms                                   Update record
                                        (completed)
                                        ────────────────────────────────────────────────►
                                        
400ms   200 OK
        {order_id: 42}
        ◄───────────────────────────────────────────────────────────────────────────────
        
        [Network timeout - response lost]
        
500ms   Retry POST /orders
        Same Idempotency-Key
        ────────────────────────────────────────────────────────────────────────────────►
        
550ms                                   Check key
                                        ────────────────────────────────────────────────►
                                        
600ms                                   Key exists
                                        Status: completed
                                        Return cached
                                        ────────────────────────────────────────────────►
                                        
650ms   200 OK
        {order_id: 42}
        (Same response, no
         duplicate order)
        ◄───────────────────────────────────────────────────────────────────────────────
```

## Key Points Illustrated

1. **Client sends request** with idempotency key
2. **Gateway checks store** before processing
3. **If key exists**, return cached response immediately
4. **If key doesn't exist**, create processing record
5. **Service processes** request (checks DB for existing order)
6. **Update store** with response on completion
7. **Retry returns** cached response, no duplicate processing

## Storage Options

### PostgreSQL (Durable, ACID)

```
┌──────────────┐
│ PostgreSQL   │
│              │
│ idempotency_ │
│ keys table   │
│              │
│ - Atomic     │
│   inserts    │
│ - Unique     │
│   constraint │
│ - TTL        │
└──────────────┘
```

### Redis (Fast, In-Memory)

```
┌──────────────┐
│    Redis     │
│              │
│ idempotency: │
│ {key}        │
│              │
│ - Low        │
│   latency    │
│ - Built-in   │
│   TTL        │
│ - High       │
│   throughput │
└──────────────┘
```

## Failure Scenarios Handled

### Scenario 1: Network Timeout After DB Write

```
Service writes to DB → Network timeout → Client retries → Returns cached response
```

### Scenario 2: Concurrent Requests

```
Request A creates processing record → Request B sees "processing" → Returns 409 Conflict
```

### Scenario 3: Key Reuse with Different Request

```
Request A: {user: "alice", amount: 100}
Request B: {user: "bob", amount: 200} (same key)
→ Rejected: "Key reused with different request"
```
