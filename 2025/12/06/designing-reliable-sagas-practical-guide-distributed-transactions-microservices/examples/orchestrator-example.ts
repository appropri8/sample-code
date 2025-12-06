import { Pool } from 'pg';
import { Kafka } from 'kafkajs';
import { SagaOrchestrator } from '../src/saga-orchestrator';
import { initializeDatabase, seedDatabase } from '../src/database';
import { OrderData } from '../src/types';

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
    clientId: 'saga-orchestrator-example',
    brokers: (process.env.KAFKA_BROKERS || 'localhost:9092').split(',')
  });

  // Initialize database
  await initializeDatabase(db);
  await seedDatabase(db);

  // Create orchestrator
  const orchestrator = new SagaOrchestrator(db, kafka);
  await orchestrator.connect();

  // Start event loop
  await orchestrator.startEventLoop();

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

  // Wait for saga to complete (in real scenario, you'd poll or use webhooks)
  console.log('Waiting for saga to complete...');
  console.log('(In production, you would poll the saga state or use webhooks)');

  // Keep process alive
  setInterval(() => {
    // Check saga state
    db.query('SELECT * FROM sagas WHERE id = $1', [sagaId])
      .then(result => {
        if (result.rows.length > 0) {
          const saga = result.rows[0];
          console.log(`Saga ${sagaId} state: ${saga.state}`);
        }
      })
      .catch(err => console.error('Error checking saga state:', err));
  }, 2000);
}

main().catch(console.error);

