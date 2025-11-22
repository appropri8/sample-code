# Multi-Region "Strong Enough" Consistency

Practical patterns for implementing "strong enough" consistency in multi-region systems. This code demonstrates per-entity guarantees, conflict handling, and observability patterns.

## Features

- **Idempotent Writes**: Prevent duplicate operations using idempotency keys
- **Optimistic Locking**: Prevent lost updates using version numbers
- **Conflict Resolution**: Merge conflicting versions of data
- **Region-Aware Routing**: Route requests to appropriate regions based on consistency requirements
- **Metrics & SLOs**: Track consistency metrics and SLO compliance

## Installation

```bash
npm install
```

## Quick Start

### Idempotent Write Endpoint

```typescript
import { IdempotentWriteService, IdempotencyStore } from './src/idempotent-write';

const store = new IdempotencyStore();
const service = new IdempotentWriteService(store);

const result = await service.processWrite(
  {
    idempotencyKey: 'payment-123-abc',
    operation: 'create_payment',
    data: { amount: 100, currency: 'USD' }
  },
  async (data) => {
    // Your payment processing logic
    return { id: 'payment-456', ...data };
  }
);
```

### Optimistic Locking

```typescript
import { OptimisticLockingService, EntityStore } from './src/optimistic-locking';

const store = new EntityStore();
const service = new OptimisticLockingService(store);

// Read entity
const entity = await service.read('account-123');

// Update with version check
try {
  const updated = await service.update({
    id: 'account-123',
    data: { balance: 1500 },
    version: entity.version
  });
} catch (error) {
  if (error instanceof VersionConflictError) {
    // Handle conflict - read again and retry
  }
}
```

### Conflict Resolution

```typescript
import { ConflictResolver, ConflictHandler } from './src/conflict-resolution';

const resolver = new ConflictResolver();
const handler = new ConflictHandler(resolver, store);

// Automatically detect and resolve conflicts
const resolved = await handler.detectAndResolve('user-123', newProfile);
```

### Region-Aware Routing

```typescript
import { RegionRouter, RegionHealthChecker } from './src/region-routing';

const router = new RegionRouter(config, healthChecker);

// Route request to appropriate region
const { region, endpoint } = await router.route({
  method: 'POST',
  path: '/api/payments',
  userId: 'user-123'
});
```

### Metrics and SLOs

```typescript
import { ObservabilityService } from './src/metrics';

const observability = new ObservabilityService(metrics, sloTracker, conflictLogger);

// Track stale read
observability.trackStaleRead('account', 'us-east', 'ap-southeast', 3000);

// Track conflict
observability.trackConflict('account-123', 'account', 'version', 'us-east');

// Check SLO violations
observability.checkSLOViolations();
```

## Examples

### Example 1: Idempotent Write

```bash
npm run example:idempotent-write
```

Shows how to:
- Accept Idempotency-Key header
- Store and reuse results
- Avoid double-charging or double-booking

### Example 2: Optimistic Locking

```bash
npm run example:optimistic-locking
```

Demonstrates:
- Entity model with version field
- Update endpoint with version check
- Handling 409 Conflict errors

### Example 3: Conflict Resolution

```bash
npm run example:conflict-resolution
```

Shows how to:
- Detect conflicts
- Merge conflicting versions
- Apply field-level merge rules

### Example 4: Region Routing

```bash
npm run example:region-routing
```

Demonstrates:
- Route to closest healthy region
- Route to primary region for strong consistency
- Handle region unavailability

### Example 5: Metrics

```bash
npm run example:metrics
```

Shows how to:
- Track stale reads
- Track conflicts
- Monitor SLO compliance

## Architecture

### Components

1. **IdempotentWriteService** (`src/idempotent-write.ts`): Handles idempotent operations
   - Accepts idempotency keys
   - Stores and reuses results
   - Prevents duplicate processing

2. **OptimisticLockingService** (`src/optimistic-locking.ts`): Prevents lost updates
   - Version-based conflict detection
   - Atomic updates with version checks
   - Clear error types

3. **ConflictResolver** (`src/conflict-resolution.ts`): Merges conflicting data
   - Field-level merge rules
   - Timestamp-based resolution
   - Support for different data types

4. **RegionRouter** (`src/region-routing.ts`): Routes requests to regions
   - Health-aware routing
   - Strong consistency routing
   - User-based sticky routing

5. **ObservabilityService** (`src/metrics.ts`): Tracks metrics and SLOs
   - Stale read tracking
   - Conflict tracking
   - SLO compliance monitoring

## Design Principles

### 1. Per-Entity Consistency

Not all data needs the same consistency guarantees. Define consistency per entity type:
- Financial data: strong consistency
- User profiles: eventual consistency
- Analytics: eventual consistency with longer delay

### 2. Clear Error Types

Use specific error types for consistency issues:
- `VersionConflictError`: Version mismatch
- `RegionUnavailableError`: Region is down
- Clear error messages and retry hints

### 3. Observability First

Track everything:
- Stale read rates
- Conflict rates
- Cross-region latency
- SLO compliance

### 4. Fail Gracefully

When consistency can't be guaranteed:
- Return clear errors
- Include retry hints
- Log for debugging
- Alert on anomalies

## Testing

Run the test suite:

```bash
npm test
```

Run with coverage:

```bash
npm test -- --coverage
```

## Production Considerations

### Storage Backends

Replace in-memory stores with:
- **Redis**: For idempotency keys and caching
- **PostgreSQL**: For durable storage
- **DynamoDB**: For distributed storage

### Health Checks

Implement real health checks:
- Database connectivity
- Cache connectivity
- Service dependencies
- Latency measurements

### Metrics Backend

Use a real metrics system:
- Prometheus
- Datadog
- CloudWatch
- Custom solution

### Conflict Resolution

For production:
- Use operational transforms for real-time collaboration
- Implement CRDTs for automatic merging
- Add human review workflows for complex conflicts

## Best Practices

1. **Start Simple**: Begin with idempotency keys and version numbers
2. **Define SLOs**: Set clear consistency guarantees per entity type
3. **Monitor Everything**: Track stale reads, conflicts, and latency
4. **Fail Closed**: When uncertain, return errors rather than stale data
5. **Document Behavior**: Tell clients what to expect
6. **Test Conflicts**: Test concurrent updates and network failures

## Limitations

- In-memory stores (extend for distributed systems)
- Simplified health checks (enhance for production)
- Basic conflict resolution (add CRDTs for complex cases)
- No authentication/authorization (add in production)

## Extending the Implementation

### Adding Database Backend

Replace in-memory stores with database:

```typescript
import { Pool } from 'pg';

class DatabaseIdempotencyStore extends IdempotencyStore {
  constructor(private pool: Pool) {
    super();
  }

  async get(key: string): Promise<IdempotencyRecord | null> {
    const result = await this.pool.query(
      'SELECT * FROM idempotency_keys WHERE key = $1 AND expires_at > NOW()',
      [key]
    );
    return result.rows[0] || null;
  }
}
```

### Adding Real Metrics Backend

Use Prometheus or similar:

```typescript
import { Counter, Histogram } from 'prom-client';

class PrometheusMetricsCollector extends MetricsCollector {
  private counters = new Map<string, Counter>();
  private histograms = new Map<string, Histogram>();

  increment(name: string, tags: Record<string, string> = {}): void {
    if (!this.counters.has(name)) {
      this.counters.set(name, new Counter({ name, labelNames: Object.keys(tags) }));
    }
    this.counters.get(name)!.inc(tags);
  }
}
```

## Contributing

When adding features:

1. Add tests for new functionality
2. Update documentation
3. Follow existing code patterns
4. Ensure proper error handling
5. Add logging for observability

## License

This code is provided as example code for educational purposes. Adapt it to your specific requirements and use cases.

