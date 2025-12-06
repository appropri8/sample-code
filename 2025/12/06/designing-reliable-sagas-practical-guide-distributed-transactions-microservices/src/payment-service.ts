import { Pool } from 'pg';
import { Kafka, Producer, Consumer } from 'kafkajs';
import { Command, SagaEvent, SagaFailureEvent, CompensationCommand } from './types';

export class PaymentService {
  private producer: Producer;
  private consumer: Consumer;
  private processedKeys: Set<string> = new Set();

  constructor(
    private db: Pool,
    private kafka: Kafka
  ) {
    this.producer = this.kafka.producer();
    this.consumer = this.kafka.consumer({ groupId: 'payment-service' });
  }

  async connect(): Promise<void> {
    await this.producer.connect();
    await this.consumer.connect();
    await this.consumer.subscribe({ topic: 'chargepayment.commands' });
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
          if (topic === 'chargepayment.commands') {
            const command: Command = JSON.parse(message.value!.toString());
            await this.handleChargePayment(command);
          } else if (topic === 'saga.compensations') {
            const compensation: CompensationCommand = JSON.parse(message.value!.toString());
            if (compensation.compensation === 'RefundPayment') {
              await this.handleRefundPayment(compensation);
            }
          }
        } catch (error) {
          console.error('Error processing message:', error);
        }
      }
    });
  }

  async handleChargePayment(command: Command): Promise<void> {
    const idempotencyKey = command.idempotencyKey;

    // Check idempotency
    if (this.processedKeys.has(idempotencyKey)) {
      console.log(`Skipping duplicate command: ${idempotencyKey}`);
      const existing = await this.getExistingPayment(command.sagaId);
      if (existing) {
        await this.publishSuccessEvent(command, existing);
      }
      return;
    }

    try {
      // Charge payment in a transaction
      const result = await this.db.query(`
        BEGIN;
        
        SELECT balance FROM accounts WHERE customer_id = $1 FOR UPDATE;
        
        UPDATE accounts 
        SET balance = balance - $2 
        WHERE customer_id = $1 AND balance >= $2
        RETURNING id, balance;
        
        INSERT INTO payments (saga_id, customer_id, amount, status)
        VALUES ($3, $1, $2, 'CHARGED')
        RETURNING id;
        
        COMMIT;
      `, [command.payload.customerId, command.payload.total, command.sagaId]);

      if (result.length === 0 || result[result.length - 1].rows.length === 0) {
        throw new Error('Insufficient funds or account not found');
      }

      const paymentId = result[result.length - 1].rows[0].id;

      // Mark as processed
      this.processedKeys.add(idempotencyKey);

      // Publish success event
      await this.publishSuccessEvent(command, { paymentId });

    } catch (error: any) {
      console.error(`Failed to charge payment for saga ${command.sagaId}:`, error);
      
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
          event: 'PaymentCharged',
          result
        } as SagaEvent)
      }]
    });
  }

  async handleRefundPayment(compensation: CompensationCommand): Promise<void> {
    try {
      // Refund payment (compensation)
      await this.db.query(`
        UPDATE accounts a
        SET balance = a.balance + p.amount
        FROM payments p
        WHERE p.saga_id = $1 AND p.customer_id = a.customer_id;
        
        UPDATE payments
        SET status = 'REFUNDED'
        WHERE saga_id = $1;
      `, [compensation.sagaId]);

      console.log(`Refunded payment for saga ${compensation.sagaId}`);

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
      console.error(`Failed to refund payment for saga ${compensation.sagaId}:`, error);
    }
  }

  private async getExistingPayment(sagaId: string): Promise<any> {
    const result = await this.db.query(
      `SELECT * FROM payments WHERE saga_id = $1 AND status = 'CHARGED'`,
      [sagaId]
    );
    return result.rows[0] || null;
  }
}

