import { Pool } from 'pg';
import { Kafka } from 'kafkajs';
import { InventoryService } from '../src/inventory-service';
import { initializeDatabase, seedDatabase } from '../src/database';

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
    clientId: 'inventory-service-example',
    brokers: (process.env.KAFKA_BROKERS || 'localhost:9092').split(',')
  });

  // Initialize database
  await initializeDatabase(db);
  await seedDatabase(db);

  // Create inventory service
  const inventoryService = new InventoryService(db, kafka);
  await inventoryService.connect();

  console.log('Inventory service started');
  console.log('Listening for ReserveInventory commands...');

  // Start processing messages
  await inventoryService.start();

  // Keep process alive
  process.on('SIGTERM', async () => {
    console.log('Shutting down inventory service...');
    await inventoryService.disconnect();
    await db.end();
    process.exit(0);
  });
}

main().catch(console.error);

