import { Pool } from 'pg';
import { Kafka, Producer, Consumer } from 'kafkajs';
import { Command, SagaEvent, SagaFailureEvent, CompensationCommand } from './types';

export class InventoryService {
  private producer: Producer;
  private consumer: Consumer;
  private processedKeys: Set<string> = new Set();

  constructor(
    private db: Pool,
    private kafka: Kafka
  ) {
    this.producer = this.kafka.producer();
    this.consumer = this.kafka.consumer({ groupId: 'inventory-service' });
  }

  async connect(): Promise<void> {
    await this.producer.connect();
    await this.consumer.connect();
    await this.consumer.subscribe({ topic: 'reserveinventory.commands' });
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
          if (topic === 'reserveinventory.commands') {
            const command: Command = JSON.parse(message.value!.toString());
            await this.handleReserveInventory(command);
          } else if (topic === 'saga.compensations') {
            const compensation: CompensationCommand = JSON.parse(message.value!.toString());
            if (compensation.compensation === 'ReleaseInventory') {
              await this.handleReleaseInventory(compensation);
            }
          }
        } catch (error) {
          console.error('Error processing message:', error);
        }
      }
    });
  }

  async handleReserveInventory(command: Command): Promise<void> {
    const idempotencyKey = command.idempotencyKey;

    // Check idempotency
    if (this.processedKeys.has(idempotencyKey)) {
      console.log(`Skipping duplicate command: ${idempotencyKey}`);
      // Return existing result
      const existing = await this.getExistingReservation(command.sagaId);
      if (existing) {
        await this.publishSuccessEvent(command, existing);
      }
      return;
    }

    try {
      // Reserve inventory in a transaction
      const result = await this.db.query(`
        BEGIN;
        
        SELECT stock FROM products WHERE id = $1 FOR UPDATE;
        
        UPDATE products 
        SET stock = stock - $2 
        WHERE id = $1 AND stock >= $2
        RETURNING id, stock;
        
        INSERT INTO reservations (saga_id, product_id, quantity, status)
        VALUES ($3, $1, $2, 'RESERVED')
        RETURNING id;
        
        COMMIT;
      `, [command.payload.productId, command.payload.quantity, command.sagaId]);

      if (result.length === 0 || result[result.length - 1].rows.length === 0) {
        throw new Error('Insufficient stock or product not found');
      }

      const reservationId = result[result.length - 1].rows[0].id;

      // Mark as processed
      this.processedKeys.add(idempotencyKey);

      // Publish success event
      await this.publishSuccessEvent(command, { reservationId });

    } catch (error: any) {
      console.error(`Failed to reserve inventory for saga ${command.sagaId}:`, error);
      
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
          event: 'InventoryReserved',
          result
        } as SagaEvent)
      }]
    });
  }

  async handleReleaseInventory(compensation: CompensationCommand): Promise<void> {
    try {
      // Release inventory (compensation)
      await this.db.query(`
        UPDATE products p
        SET stock = p.stock + r.quantity
        FROM reservations r
        WHERE r.saga_id = $1 AND r.product_id = p.id;
        
        UPDATE reservations
        SET status = 'RELEASED'
        WHERE saga_id = $1;
      `, [compensation.sagaId]);

      console.log(`Released inventory for saga ${compensation.sagaId}`);

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
      console.error(`Failed to release inventory for saga ${compensation.sagaId}:`, error);
    }
  }

  private async getExistingReservation(sagaId: string): Promise<any> {
    const result = await this.db.query(
      `SELECT * FROM reservations WHERE saga_id = $1 AND status = 'RESERVED'`,
      [sagaId]
    );
    return result.rows[0] || null;
  }
}

