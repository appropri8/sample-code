/**
 * Queue consumer with idempotency
 * 
 * This example shows how to process messages from Kafka
 * with idempotency to prevent duplicate processing.
 */

import { Kafka } from 'kafkajs';
import { Pool } from 'pg';
import { IdempotentQueueConsumer } from '../src/queue-consumer';

async function main() {
  const kafka = new Kafka({
    clientId: 'order-consumer',
    brokers: process.env.KAFKA_BROKERS?.split(',') || ['localhost:9092'],
  });

  const pool = new Pool({
    host: process.env.DB_HOST || 'localhost',
    port: parseInt(process.env.DB_PORT || '5432'),
    database: process.env.DB_NAME || 'idempotency_db',
    user: process.env.DB_USER || 'postgres',
    password: process.env.DB_PASSWORD || 'postgres',
  });

  const consumer = new IdempotentQueueConsumer(
    kafka,
    'order-processing-group',
    pool
  );

  await consumer.connect();
  await consumer.subscribe('orders');

  console.log('Consumer connected, waiting for messages...');

  await consumer.run(async (payload) => {
    await consumer.processOrderMessage(payload);
  });

  // Graceful shutdown
  process.on('SIGINT', async () => {
    console.log('Shutting down...');
    await consumer.disconnect();
    await pool.end();
    process.exit(0);
  });
}

main().catch((error) => {
  console.error('Consumer error:', error);
  process.exit(1);
});
