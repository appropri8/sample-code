import { Pool } from 'pg';
import { Kafka, Producer, Consumer } from 'kafkajs';
import { Command, SagaEvent, SagaFailureEvent, CompensationCommand } from './types';

export class OrderService {
  private producer: Producer;
  private consumer: Consumer;
  private processedKeys: Set<string> = new Set();

  constructor(
    private db: Pool,
    private kafka: Kafka
  ) {
    this.producer = this.kafka.producer();
    this.consumer = this.kafka.consumer({ groupId: 'order-service' });
  }

  async connect(): Promise<void> {
    await this.producer.connect();
    await this.consumer.connect();
    await this.consumer.subscribe({ topic: 'confirmorder.commands' });
    await this.consumer.subscribe({ topic: 'saga.compensations' });
  }

  async disconnect(): Promise<void> {
    await this.producer.disconnect();
    await this.consumer.disconnect();
  }

  async start(): Promise<void> {
    await this.consumer.run({
      eachMessage: async ({ topic, message }) => {
        try {
          if (topic === 'confirmorder.commands') {
            const command: Command = JSON.parse(message.value!.toString());
            await this.handleConfirmOrder(command);
          } else if (topic === 'saga.compensations') {
            const compensation: CompensationCommand = JSON.parse(message.value!.toString());
            if (compensation.compensation === 'CancelOrder') {
              await this.handleCancelOrder(compensation);
            }
          }
        } catch (error) {
          console.error('Error processing message:', error);
        }
      }
    });
  }

  async handleConfirmOrder(command: Command): Promise<void> {
    const idempotencyKey = command.idempotencyKey;

    // Check idempotency
    if (this.processedKeys.has(idempotencyKey)) {
      console.log(`Skipping duplicate command: ${idempotencyKey}`);
      const existing = await this.getExistingOrder(command.sagaId);
      if (existing) {
        await this.publishSuccessEvent(command, existing);
      }
      return;
    }

    try {
      // Confirm order in a transaction
      const result = await this.db.query(`
        UPDATE orders
        SET status = 'CONFIRMED', confirmed_at = NOW()
        WHERE saga_id = $1
        RETURNING id, status;
      `, [command.sagaId]);

      if (result.rows.length === 0) {
        throw new Error('Order not found');
      }

      // Mark as processed
      this.processedKeys.add(idempotencyKey);

      // Publish success event
      await this.publishSuccessEvent(command, { orderId: result.rows[0].id });

    } catch (error: any) {
      console.error(`Failed to confirm order for saga ${command.sagaId}:`, error);
      
      // Publish failure event
      await this.producer.send({
        topic: 'saga.failures',
        messages: [{
          key: command.sagaId,
          value: JSON.stringify({
            sagaId: command.sagaId,
            stepSequence: command.stepSequence,
            error: error.message
          } as SagaFailureEvent)
        }]
      });
    }
  }

  private async publishSuccessEvent(command: Command, result: any): Promise<void> {
    await this.producer.send({
      topic: 'saga.events',
      messages: [{
        key: command.sagaId,
        value: JSON.stringify({
          sagaId: command.sagaId,
          stepSequence: command.stepSequence,
          event: 'OrderConfirmed',
          result
        } as SagaEvent)
      }]
    });
  }

  async handleCancelOrder(compensation: CompensationCommand): Promise<void> {
    try {
      // Cancel order (compensation)
      await this.db.query(`
        UPDATE orders
        SET status = 'CANCELLED', cancelled_at = NOW()
        WHERE saga_id = $1;
      `, [compensation.sagaId]);

      console.log(`Cancelled order for saga ${compensation.sagaId}`);

      // Publish compensation completed event
      await this.producer.send({
        topic: 'saga.compensations.completed',
        messages: [{
          key: compensation.sagaId,
          value: JSON.stringify({
            sagaId: compensation.sagaId,
            stepName: compensation.stepName,
            status: 'COMPENSATED'
          })
        }]
      });
    } catch (error) {
      console.error(`Failed to cancel order for saga ${compensation.sagaId}:`, error);
    }
  }

  private async getExistingOrder(sagaId: string): Promise<any> {
    const result = await this.db.query(
      `SELECT * FROM orders WHERE saga_id = $1 AND status = 'CONFIRMED'`,
      [sagaId]
    );
    return result.rows[0] || null;
  }
}

