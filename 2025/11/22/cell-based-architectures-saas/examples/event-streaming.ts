import { InMemoryEventStream } from '../src/event-stream';
import { EventPublisher } from '../src/event-publisher';

async function main() {
  console.log('=== Event Streaming Example ===\n');

  // Create event stream
  const eventStream = new InMemoryEventStream();

  // Create publishers for different cells
  const publisher1 = new EventPublisher('cell-1', eventStream);
  const publisher2 = new EventPublisher('cell-2', eventStream);
  const publisher3 = new EventPublisher('cell-3', eventStream);

  // Publish events
  console.log('Publishing events...\n');

  await publisher1.publishEvent('OrderCreated', 'tenant-1', {
    orderId: 'order-123',
    amount: 99.99,
    items: ['item-1', 'item-2']
  });
  console.log('Published OrderCreated from cell-1 for tenant-1');

  await publisher2.publishEvent('OrderCreated', 'tenant-2', {
    orderId: 'order-456',
    amount: 149.99,
    items: ['item-3']
  });
  console.log('Published OrderCreated from cell-2 for tenant-2');

  await publisher1.publishEvent('UserSignedUp', 'tenant-1', {
    userId: 'user-789',
    email: 'user@example.com'
  });
  console.log('Published UserSignedUp from cell-1 for tenant-1');

  await publisher3.publishEvent('OrderCreated', 'tenant-3', {
    orderId: 'order-789',
    amount: 199.99,
    items: ['item-4', 'item-5', 'item-6']
  });
  console.log('Published OrderCreated from cell-3 for tenant-3');

  // Consume events
  console.log('\nConsuming events...\n');

  const events = eventStream.getEvents('tenant-events');
  console.log(`Total events: ${events.length}\n`);

  events.forEach((event, index) => {
    console.log(`Event ${index + 1}:`);
    console.log(`  Type: ${event.type}`);
    console.log(`  Tenant: ${event.tenantId}`);
    console.log(`  Cell: ${event.cellId}`);
    console.log(`  Data:`, event.data);
    console.log(`  Timestamp: ${new Date(event.timestamp).toISOString()}`);
    console.log();
  });

  // Aggregate by event type
  console.log('Aggregating by event type...\n');
  const byType = new Map<string, number>();
  events.forEach(event => {
    const count = byType.get(event.type) || 0;
    byType.set(event.type, count + 1);
  });

  byType.forEach((count, type) => {
    console.log(`  ${type}: ${count} events`);
  });

  // Aggregate by cell
  console.log('\nAggregating by cell...\n');
  const byCell = new Map<string, number>();
  events.forEach(event => {
    const count = byCell.get(event.cellId) || 0;
    byCell.set(event.cellId, count + 1);
  });

  byCell.forEach((count, cellId) => {
    console.log(`  ${cellId}: ${count} events`);
  });

  // Aggregate by tenant
  console.log('\nAggregating by tenant...\n');
  const byTenant = new Map<string, number>();
  events.forEach(event => {
    const count = byTenant.get(event.tenantId) || 0;
    byTenant.set(event.tenantId, count + 1);
  });

  byTenant.forEach((count, tenantId) => {
    console.log(`  ${tenantId}: ${count} events`);
  });

  // Simulate analytics consumer
  console.log('\nSimulating analytics consumer...\n');
  let orderCount = 0;
  let totalRevenue = 0;

  events.forEach(event => {
    if (event.type === 'OrderCreated') {
      orderCount++;
      totalRevenue += event.data.amount;
    }
  });

  console.log(`Total orders: ${orderCount}`);
  console.log(`Total revenue: $${totalRevenue.toFixed(2)}`);

  console.log('\n=== Example Complete ===');
}

main().catch(console.error);


