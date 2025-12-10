import { Kafka, Consumer, EachMessagePayload } from 'kafkajs';
import { Pool } from 'pg';
import { OrderService } from './order-service';
import { CreateOrderRequest } from './types';

export class IdempotentQueueConsumer {
  private consumer: Consumer;
  private pool: Pool;
  private orderService: OrderService;

  constructor(
    kafka: Kafka,
    groupId: string,
    pool: Pool
  ) {
    this.consumer = kafka.consumer({ groupId });
    this.pool = pool;
    this.orderService = new OrderService(pool);
  }

  async connect(): Promise<void> {
    await this.consumer.connect();
  }

  async disconnect(): Promise<void> {
    await this.consumer.disconnect();
  }

  async subscribe(topic: string): Promise<void> {
    await this.consumer.subscribe({ topic, fromBeginning: false });
  }

  async run(
    handler: (payload: EachMessagePayload) => Promise<void>
  ): Promise<void> {
    await this.consumer.run({
      eachMessage: async (payload) => {
        try {
          await handler(payload);
        } catch (error) {
          console.error('Error processing message:', error);
          // In production, you might want to send to DLQ
        }
      },
    });
  }

  async processOrderMessage(payload: EachMessagePayload): Promise<void> {
    const message = payload.message;
    const idempotencyKey = message.headers?.['idempotency-key']?.toString();

    if (!idempotencyKey) {
      console.warn('Message missing idempotency key, skipping');
      return;
    }

    // Check if already processed
    const processed = await this.pool.query(
      `SELECT * FROM processed_messages 
       WHERE idempotency_key = $1`,
      [idempotencyKey]
    );

    if (processed.rows.length > 0) {
      console.log(`Already processed message: ${idempotencyKey}`);
      return; // Skip duplicate
    }

    // Parse message
    const orderRequest: CreateOrderRequest = JSON.parse(
      message.value?.toString() || '{}'
    );

    // Process order
    const order = await this.orderService.createOrder(
      orderRequest,
      idempotencyKey
    );

    // Mark as processed
    await this.pool.query(
      `INSERT INTO processed_messages 
       (idempotency_key, topic, partition, offset)
       VALUES ($1, $2, $3, $4)
       ON CONFLICT (idempotency_key) DO NOTHING`,
      [
        idempotencyKey,
        payload.topic,
        payload.partition,
        message.offset,
      ]
    );

    console.log(`Processed order: ${order.order_id}`);
  }
}

// Example usage
export async function startOrderConsumer() {
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
  
  await consumer.run(async (payload) => {
    await consumer.processOrderMessage(payload);
  });

  console.log('Order consumer started');
}
