import pino from 'pino';

export interface StructuredLog {
  tenantId?: string;
  desiredGeneration?: number;
  observedGeneration?: number;
  action?: string;
  provider?: string;
  idempotencyKey?: string;
  externalResourceId?: string;
  outcome?: string;
  nextReconcileAt?: string;
  durationMs?: number;
  error?: string;
}

export const logger = pino({
  level: process.env.LOG_LEVEL || 'info',
  formatter: (log) => {
    return {
      timestamp: new Date().toISOString(),
      ...log,
    };
  },
});

export function logReconciliationEntry(entry: StructuredLog): void {
  logger.info(entry);
}