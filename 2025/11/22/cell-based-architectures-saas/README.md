# Cell-Based Architectures for SaaS: Designing for Blast Radius

A TypeScript implementation demonstrating cell-based architecture for multi-tenant SaaS systems. This code shows how to isolate tenants into self-contained cells to limit blast radius and improve system reliability.

## Features

- **Cell Directory**: Map tenants to cells with caching and TTL
- **Cell Router**: Route requests to the correct cell based on tenant ID
- **Control Plane API**: Manage cells, assign tenants, and handle provisioning
- **Event Streaming**: Publish tenant events to global analytics
- **Tenant Rebalancing**: Move tenants between cells with data migration
- **Health Checks**: Monitor cell health and update routing accordingly

## Installation

```bash
npm install
```

## Quick Start

### Basic Cell Routing

```typescript
import { CellDirectory } from './src/cell-directory';
import { CellRouter } from './src/cell-router';
import { ControlPlaneAPI } from './src/control-plane';

// Create control plane
const controlPlane = new ControlPlaneAPI();

// Create cell directory
const directory = new CellDirectory(controlPlane);

// Create router
const cellBaseUrls = new Map([
  ['cell-1', 'http://cell-1.internal'],
  ['cell-2', 'http://cell-2.internal'],
  ['cell-3', 'http://cell-3.internal']
]);
const router = new CellRouter(directory, cellBaseUrls);

// Route a request
const request = {
  headers: {
    'authorization': 'Bearer eyJ0ZW5hbnRJZCI6InRlbmFudC0xMjMifQ==',
    'host': 'api.example.com'
  },
  method: 'GET',
  url: 'https://api.example.com/orders'
};

const response = await router.route(request);
console.log(response);
```

### Creating Cells

```typescript
// Create a new cell
const cell = await controlPlane.createCell({
  id: 'cell-4',
  capacity: 1000
});

console.log(`Created cell: ${cell.id}`);

// Assign tenant to cell
await controlPlane.assignTenantToCell('tenant-123', 'cell-4');
```

### Event Publishing

```typescript
import { EventPublisher } from './src/event-publisher';
import { EventStream } from './src/event-stream';

const eventStream = new EventStream('tenant-events');
const publisher = new EventPublisher('cell-1', eventStream);

// Publish an event
await publisher.publishEvent('OrderCreated', 'tenant-123', {
  orderId: 'order-456',
  amount: 99.99,
  items: ['item-1', 'item-2']
});
```

## Examples

### Example 1: Basic Routing

```bash
npm run example:basic-routing
```

Shows how to:
- Extract tenant ID from requests
- Look up cell for tenant
- Route request to correct cell
- Handle errors gracefully

### Example 2: Control Plane Operations

```bash
npm run example:control-plane
```

Demonstrates:
- Creating new cells
- Assigning tenants to cells
- Updating cell status
- Querying cell information

### Example 3: Event Streaming

```bash
npm run example:event-streaming
```

Shows how to:
- Publish events from cells
- Consume events for analytics
- Aggregate data across cells

### Example 4: Tenant Rebalancing

```bash
npm run example:rebalancing
```

Demonstrates:
- Moving tenants between cells
- Data migration
- Routing updates
- Verification

## Architecture

### Components

1. **CellDirectory** (`src/cell-directory.ts`): Maps tenants to cells
   - Caches mappings with TTL
   - Supports hash-based and rules-based routing
   - Handles VIP and enterprise tenants

2. **CellRouter** (`src/cell-router.ts`): Routes requests to cells
   - Extracts tenant ID from JWT, headers, or subdomain
   - Forwards requests to correct cell
   - Handles cell unavailability

3. **ControlPlaneAPI** (`src/control-plane.ts`): Manages cells
   - Create and manage cells
   - Assign tenants to cells
   - Track cell capacity and status
   - Emit provisioning events

4. **EventPublisher** (`src/event-publisher.ts`): Publishes tenant events
   - Publishes events to global stream
   - Includes cell ID and tenant ID
   - Supports various event types

5. **EventStream** (`src/event-stream.ts`): Global event stream
   - Publishes events
   - Consumes events for analytics
   - In-memory implementation (extend for production)

6. **TenantRebalancer** (`src/tenant-rebalancer.ts`): Moves tenants
   - Migrates tenant data between cells
   - Updates routing
   - Verifies data integrity
   - Handles traffic draining

## Design Principles

### 1. Isolation

Each cell is completely isolated. Services, databases, caches, and queues are independent. A problem in one cell doesn't affect others.

### 2. Blast Radius Control

When something breaks, only tenants in that cell are affected. The rest of the system keeps running.

### 3. Simple Routing

Start with simple routing logic. Hash-based or basic rules. Add complexity only when needed.

### 4. Caching

Cache tenant-to-cell mappings aggressively. The control plane should be read-heavy, not write-heavy.

### 5. Event-Driven

Use events for coordination between cells. Keep cells loosely coupled.

## Testing

Run the test suite:

```bash
npm test
```

Run with coverage:

```bash
npm test -- --coverage
```

## Configuration

### Cell Configuration

Cells can be configured with different capacities and tiers:

```typescript
await controlPlane.createCell({
  id: 'cell-enterprise-1',
  capacity: 100,  // Max tenants
  tier: 'enterprise'
});
```

### Routing Rules

Configure routing rules in `CellDirectory`:

```typescript
// VIP tenants get dedicated cells
if (tenant.tier === 'vip') {
  return `cell-vip-${hashString(tenant.id) % 10}`;
}

// Enterprise tenants share cells
if (tenant.tier === 'enterprise') {
  return `cell-enterprise-${hashString(tenant.id) % 20}`;
}

// Regular tenants use shared cells
return `cell-shared-${hashString(tenant.id) % 100}`;
```

## Best Practices

1. **Start Small**: Begin with 2-3 cells. Learn and iterate.

2. **Cache Aggressively**: Cache tenant-to-cell mappings. Use long TTLs.

3. **Monitor Health**: Check cell health regularly. Update routing when cells are unhealthy.

4. **Fail Closed**: When routing is uncertain, return an error. Better safe than wrong.

5. **Event Streaming**: Use events for cross-cell coordination. Keep cells independent.

6. **Gradual Migration**: Move tenants gradually. Verify after each move.

7. **Data Integrity**: Always verify data after migration. Compare record counts and samples.

## Production Considerations

### Distributed Control Plane

For production, use a distributed control plane:

- Use Redis or a database for tenant directory
- Replicate control plane data
- Use distributed locks for updates

### Real Event Streaming

Replace in-memory event stream with:

- Apache Kafka
- AWS Kinesis
- Google Pub/Sub
- RabbitMQ

### Database Migrations

Implement proper database migration tools:

- Use migration frameworks (e.g., Knex, TypeORM)
- Support forward-compatible migrations
- Test migrations on staging first

### Health Checks

Implement comprehensive health checks:

- Check database connectivity
- Check cache connectivity
- Check service health
- Check queue depth

### Monitoring

Add monitoring for:

- Cell capacity utilization
- Request routing errors
- Cell health status
- Migration success rates
- Event publishing latency

## Limitations

- In-memory control plane (extend for distributed systems)
- In-memory event stream (use Kafka/Kinesis in production)
- Simulated data migration (implement real database migration)
- Basic health checks (enhance for production)
- No authentication/authorization (add in production)

## Extending the Implementation

### Adding Database Backend

Replace in-memory storage with a database:

```typescript
import { Database } from 'your-db-library';

class DatabaseControlPlane extends ControlPlaneAPI {
  constructor(private db: Database) {
    super();
  }
  
  async getCellForTenant(tenantId: string): Promise<string> {
    const result = await this.db.query(
      'SELECT cell_id FROM tenant_cells WHERE tenant_id = ?',
      [tenantId]
    );
    return result.cell_id;
  }
}
```

### Adding Real Event Streaming

Use Kafka for event streaming:

```typescript
import { Kafka } from 'kafkajs';

class KafkaEventStream implements EventStream {
  private producer: KafkaProducer;
  
  async publish(topic: string, event: TenantEvent): Promise<void> {
    await this.producer.send({
      topic,
      messages: [{ value: JSON.stringify(event) }]
    });
  }
}
```

### Adding Data Migration

Implement real database migration:

```typescript
class DatabaseMigrator implements DataMigrator {
  async migrateTenantData(
    tenantId: string,
    sourceCell: string,
    targetCell: string
  ): Promise<void> {
    // Connect to source database
    const sourceDb = await this.getCellDatabase(sourceCell);
    
    // Connect to target database
    const targetDb = await this.getCellDatabase(targetCell);
    
    // Copy all tenant data
    const tables = ['orders', 'users', 'products'];
    for (const table of tables) {
      const data = await sourceDb.query(
        `SELECT * FROM ${table} WHERE tenant_id = ?`,
        [tenantId]
      );
      
      for (const row of data) {
        await targetDb.query(
          `INSERT INTO ${table} VALUES ?`,
          [row]
        );
      }
    }
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


