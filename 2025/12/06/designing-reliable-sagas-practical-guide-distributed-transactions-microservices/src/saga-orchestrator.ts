import { Pool } from 'pg';
import { Kafka, Producer, Consumer } from 'kafkajs';
import { generateId, generateIdempotencyKey } from './utils';
import {
  SagaState,
  SagaRecord,
  SagaStepRecord,
  Command,
  SagaEvent,
  SagaFailureEvent,
  CompensationCommand,
  OrderData
} from './types';

export class SagaOrchestrator {
  private producer: Producer;
  private consumer: Consumer;
  private readonly STEP_TIMEOUT = 30000; // 30 seconds

  constructor(
    private db: Pool,
    private kafka: Kafka
  ) {
    this.producer = this.kafka.producer();
    this.consumer = this.kafka.consumer({ groupId: 'saga-orchestrator' });
  }

  async connect(): Promise<void> {
    await this.producer.connect();
    await this.consumer.connect();
    await this.consumer.subscribe({ topic: 'saga.events' });
    await this.consumer.subscribe({ topic: 'saga.failures' });
  }

  async disconnect(): Promise<void> {
    await this.producer.disconnect();
    await this.consumer.disconnect();
  }

  async startSaga(sagaType: string, payload: OrderData): Promise<string> {
    const sagaId = generateId();

    // Create saga record
    await this.db.query(
      `INSERT INTO sagas (id, state, type, payload, started_at)
       VALUES ($1, $2, $3, $4, NOW())`,
      [sagaId, 'PENDING', sagaType, JSON.stringify(payload)]
    );

    // Publish initial command
    await this.producer.send({
      topic: 'reserveinventory.commands',
      messages: [{
        key: sagaId,
        value: JSON.stringify({
          sagaId,
          stepSequence: 1,
          command: 'ReserveInventory',
          idempotencyKey: generateIdempotencyKey(sagaId, 1),
          payload
        } as Command)
      }]
    });

    // Create initial step record
    await this.db.query(
      `INSERT INTO saga_steps (saga_id, step_name, step_sequence, status)
       VALUES ($1, $2, $3, 'PENDING')`,
      [sagaId, 'ReserveInventory', 1]
    );

    console.log(`Started saga ${sagaId} of type ${sagaType}`);
    return sagaId;
  }

  async handleEvent(event: SagaEvent): Promise<void> {
    const saga = await this.getSaga(event.sagaId);
    if (!saga) {
      console.error(`Saga ${event.sagaId} not found`);
      return;
    }

    // Update step status
    await this.updateStepStatus(
      event.sagaId,
      event.stepSequence,
      'COMPLETED',
      event.result
    );

    // Determine next step
    const nextStep = this.getNextStep(saga.type, event.stepSequence);

    if (nextStep) {
      await this.executeNextStep(saga.id, nextStep, JSON.parse(saga.payload));
    } else {
      // Saga complete
      await this.completeSaga(saga.id);
    }
  }

  async handleFailure(event: SagaFailureEvent): Promise<void> {
    const saga = await this.getSaga(event.sagaId);
    if (!saga) {
      console.error(`Saga ${event.sagaId} not found`);
      return;
    }

    // Mark step as failed
    await this.updateStepStatus(
      event.sagaId,
      event.stepSequence,
      'FAILED',
      null,
      event.error
    );

    // Trigger compensation
    await this.compensate(saga.id);
  }

  private async compensate(sagaId: string): Promise<void> {
    console.log(`Starting compensation for saga ${sagaId}`);

    const steps = await this.getCompletedSteps(sagaId);

    // Compensate in reverse order
    for (const step of steps.reverse()) {
      const compensationCommand: CompensationCommand = {
        sagaId,
        stepName: step.step_name,
        compensation: this.getCompensationCommand(step.step_name),
        payload: step.result
      };

      await this.producer.send({
        topic: 'saga.compensations',
        messages: [{
          key: sagaId,
          value: JSON.stringify(compensationCommand)
        }]
      });

      // Mark step as compensated
      await this.updateStepStatus(
        sagaId,
        step.step_sequence,
        'COMPENSATED'
      );
    }

    // Mark saga as compensated
    await this.db.query(
      `UPDATE sagas SET state = 'COMPENSATED', compensated_at = NOW()
       WHERE id = $1`,
      [sagaId]
    );

    console.log(`Compensation completed for saga ${sagaId}`);
  }

  private async getSaga(sagaId: string): Promise<SagaRecord | null> {
    const result = await this.db.query(
      `SELECT * FROM sagas WHERE id = $1`,
      [sagaId]
    );
    return result.rows[0] || null;
  }

  private async updateStepStatus(
    sagaId: string,
    stepSequence: number,
    status: string,
    result?: any,
    error?: string
  ): Promise<void> {
    if (status === 'COMPLETED') {
      await this.db.query(
        `UPDATE saga_steps 
         SET status = $1, result = $2, completed_at = NOW()
         WHERE saga_id = $3 AND step_sequence = $4`,
        [status, JSON.stringify(result), sagaId, stepSequence]
      );
    } else if (status === 'FAILED') {
      await this.db.query(
        `UPDATE saga_steps 
         SET status = $1, error = $2, failed_at = NOW()
         WHERE saga_id = $3 AND step_sequence = $4`,
        [status, error, sagaId, stepSequence]
      );
    } else if (status === 'COMPENSATED') {
      await this.db.query(
        `UPDATE saga_steps 
         SET status = $1
         WHERE saga_id = $2 AND step_sequence = $3`,
        [status, sagaId, stepSequence]
      );
    }
  }

  private getNextStep(sagaType: string, currentStep: number): string | null {
    const steps: Record<string, string[]> = {
      'OrderCheckout': [
        'ReserveInventory',
        'ChargePayment',
        'ConfirmOrder'
      ]
    };

    const sagaSteps = steps[sagaType] || [];
    const nextIndex = currentStep;

    if (nextIndex >= sagaSteps.length) {
      return null;
    }

    return sagaSteps[nextIndex];
  }

  private async executeNextStep(
    sagaId: string,
    stepName: string,
    payload: any
  ): Promise<void> {
    // Get current step sequence
    const stepResult = await this.db.query(
      `SELECT MAX(step_sequence) as max_seq FROM saga_steps WHERE saga_id = $1`,
      [sagaId]
    );
    const nextSequence = (stepResult.rows[0].max_seq || 0) + 1;

    // Create step record
    await this.db.query(
      `INSERT INTO saga_steps (saga_id, step_name, step_sequence, status)
       VALUES ($1, $2, $3, 'PENDING')`,
      [sagaId, stepName, nextSequence]
    );

    // Determine topic based on step name
    const topic = this.getTopicForStep(stepName);

    // Publish command
    await this.producer.send({
      topic,
      messages: [{
        key: sagaId,
        value: JSON.stringify({
          sagaId,
          stepSequence: nextSequence,
          command: stepName,
          payload,
          idempotencyKey: generateIdempotencyKey(sagaId, nextSequence)
        } as Command)
      }]
    });

    console.log(`Published command for step ${stepName} in saga ${sagaId}`);
  }

  private getTopicForStep(stepName: string): string {
    const topicMap: Record<string, string> = {
      'ReserveInventory': 'reserveinventory.commands',
      'ChargePayment': 'chargepayment.commands',
      'ConfirmOrder': 'confirmorder.commands'
    };
    return topicMap[stepName] || `${stepName.toLowerCase()}.commands`;
  }

  private async getCompletedSteps(sagaId: string): Promise<SagaStepRecord[]> {
    const result = await this.db.query(
      `SELECT * FROM saga_steps 
       WHERE saga_id = $1 AND status = 'COMPLETED'
       ORDER BY step_sequence ASC`,
      [sagaId]
    );
    return result.rows;
  }

  private getCompensationCommand(stepName: string): string {
    const compensations: Record<string, string> = {
      'ReserveInventory': 'ReleaseInventory',
      'ChargePayment': 'RefundPayment',
      'ConfirmOrder': 'CancelOrder'
    };
    return compensations[stepName] || 'Unknown';
  }

  private async completeSaga(sagaId: string): Promise<void> {
    await this.db.query(
      `UPDATE sagas SET state = 'COMPLETED', completed_at = NOW()
       WHERE id = $1`,
      [sagaId]
    );
    console.log(`Saga ${sagaId} completed successfully`);
  }

  async startEventLoop(): Promise<void> {
    await this.consumer.run({
      eachMessage: async ({ topic, message }) => {
        try {
          if (topic === 'saga.events') {
            const event: SagaEvent = JSON.parse(message.value!.toString());
            await this.handleEvent(event);
          } else if (topic === 'saga.failures') {
            const event: SagaFailureEvent = JSON.parse(message.value!.toString());
            await this.handleFailure(event);
          }
        } catch (error) {
          console.error('Error processing message:', error);
        }
      }
    });
  }
}

