export type SagaState = 
  | 'PENDING'
  | 'RESERVED'
  | 'CHARGED'
  | 'SHIPPED'
  | 'COMPLETED'
  | 'FAILED'
  | 'COMPENSATED';

export interface SagaStep {
  name: string;
  status: 'PENDING' | 'COMPLETED' | 'FAILED' | 'COMPENSATED';
  completedAt?: Date;
  failedAt?: Date;
  error?: string;
  result?: any;
}

export interface Saga {
  id: string;
  state: SagaState;
  steps: SagaStep[];
  startedAt: Date;
  completedAt?: Date;
  compensatedAt?: Date;
  payload: any;
}

export interface SagaRecord {
  id: string;
  state: SagaState;
  type: string;
  payload: any;
  started_at: Date;
  completed_at?: Date;
  compensated_at?: Date;
}

export interface SagaStepRecord {
  id: number;
  saga_id: string;
  step_name: string;
  step_sequence: number;
  status: 'PENDING' | 'COMPLETED' | 'FAILED' | 'COMPENSATED';
  result?: any;
  error?: string;
  completed_at?: Date;
  failed_at?: Date;
}

export interface Command {
  sagaId: string;
  stepSequence: number;
  command: string;
  idempotencyKey: string;
  payload: any;
}

export interface SagaEvent {
  sagaId: string;
  stepSequence: number;
  event: string;
  result?: any;
}

export interface SagaFailureEvent {
  sagaId: string;
  stepSequence: number;
  error: string;
}

export interface CompensationCommand {
  sagaId: string;
  stepName: string;
  compensation: string;
  payload: any;
}

export interface OrderData {
  productId: string;
  quantity: number;
  customerId: string;
  total: number;
}

