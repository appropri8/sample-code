import { v4 as uuidv4 } from 'uuid';

export function generateId(): string {
  return uuidv4();
}

export function generateIdempotencyKey(sagaId: string, stepSequence: number): string {
  return `${sagaId}-${stepSequence}`;
}

export function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

export function isRetryableError(error: Error): boolean {
  const retryableMessages = ['timeout', 'network', 'ECONNREFUSED', 'ETIMEDOUT', 'ECONNRESET'];
  return retryableMessages.some(msg => error.message.includes(msg));
}

