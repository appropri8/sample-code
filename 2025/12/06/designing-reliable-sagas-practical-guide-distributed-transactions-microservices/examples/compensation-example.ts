import { Pool } from 'pg';
import { Kafka } from 'kafkajs';
import { SagaOrchestrator } from '../src/saga-orchestrator';
import { InventoryService } from '../src/inventory-service';
import { PaymentService } from '../src/payment-service';
import { OrderService } from '../src/order-service';
import { initializeDatabase, seedDatabase } from '../src/database';
import { OrderData } from '../src/types';

/**
 * This example demonstrates compensation handling.
 * It starts a saga and then simulates a failure to trigger compensation.
 */
async function main() {
  // Database connection
  const db = new Pool({
    host: process.env.DB_HOST || 'localhost',
    port: parseInt(process.env.DB_PORT || '5432'),
    database: process.env.DB_NAME || 'saga_db',
    user: process.env.DB_USER || 'postgres',
    password: process.env.DB_PASSWORD || 'postgres'
  });

  // Kafka connection
  const kafka = new Kafka({
    clientId: 'compensation-example',
    brokers: (process.env.KAFKA_BROKERS || 'localhost:9092').split(',')
  });

  // Initialize database
  await initializeDatabase(db);
  await seedDatabase(db);

  // Create services
  const orchestrator = new SagaOrchestrator(db, kafka);
  const inventoryService = new InventoryService(db, kafka);
  const paymentService = new PaymentService(db, kafka);
  const orderService = new OrderService(db, kafka);

  // Connect services
  await orchestrator.connect();
  await inventoryService.connect();
  await paymentService.connect();
  await orderService.connect();

  // Start event loops
  await orchestrator.startEventLoop();
  await inventoryService.start();
  await paymentService.start();
  await orderService.start();

  // Start a saga
  const orderData: OrderData = {
    productId: 'prod-1',
    quantity: 2,
    customerId: 'cust-1',
    total: 100.00
  };

  console.log('Starting order checkout saga...');
  const sagaId = await orchestrator.startSaga('OrderCheckout', orderData);
  console.log(`Saga started with ID: ${sagaId}`);

  // Simulate a failure after a delay (in real scenario, this would be a service failure)
  setTimeout(async () => {
    console.log('Simulating payment failure...');
    // Manually trigger a failure event
    const producer = kafka.producer();
    await producer.connect();
    await producer.send({
      topic: 'saga.failures',
      messages: [{
        key: sagaId,
        value: JSON.stringify({
          sagaId,
          stepSequence: 2, // Payment step
          error: 'Payment service unavailable'
        })
      }]
    });
    await producer.disconnect();
  }, 5000);

  // Monitor saga state
  const interval = setInterval(async () => {
    const result = await db.query('SELECT * FROM sagas WHERE id = $1', [sagaId]);
    if (result.rows.length > 0) {
      const saga = result.rows[0];
      console.log(`Saga ${sagaId} state: ${saga.state}`);
      
      if (saga.state === 'COMPENSATED' || saga.state === 'COMPLETED') {
        clearInterval(interval);
        console.log('Saga finished. Shutting down...');
        await orchestrator.disconnect();
        await inventoryService.disconnect();
        await paymentService.disconnect();
        await orderService.disconnect();
        await db.end();
        process.exit(0);
      }
    }
  }, 1000);
}

main().catch(console.error);

