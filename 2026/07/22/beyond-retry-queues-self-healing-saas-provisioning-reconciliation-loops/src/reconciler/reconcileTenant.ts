import { TenantRow } from '../models/tenant';
import { TenantRepository } from '../db/client';
import { Executor } from './executor';
import { calculatePlan, calculateDeletionPlan } from './planner';
import { calculateBackoff } from './backoff';
import { RetryableError, TerminalError } from './errors';
import { ConcurrencyLock } from './lock';
import { CircuitBreaker } from '../utils/circuit-breaker';
import { logger } from '../utils/logging';

export class Reconciler {
  private circuitBreakers = new Map<string, CircuitBreaker>();

  constructor(
    private readonly repository: TenantRepository,
    private readonly executor: Executor,
    private readonly lock: ConcurrencyLock
  ) {}

  async reconcile(tenantId: string): Promise<ReconcileOutcome> {
    const acquired = await this.lock.acquire(tenantId, 30000);
    if (!acquired) {
      return { outcome: 'requeue', delayMs: 1000 };
    }

    try {
      const tenant = await this.repository.lockTenant(tenantId);
      if (!tenant) {
        return { outcome: 'complete', delayMs: 0 };
      }

      if (tenant.provisioningStatus === 'deleting') {
        return this.processDeletion(tenant);
      }

      if (tenant.terminalError && tenant.failureCount >= 5) {
        const breaker = this.getCircuitBreaker(tenantId);
        if (breaker.allowRequest()) {
          await this.repository.recordObservation(tenantId, {
            failureCount: 0,
            lastErrorCode: undefined,
            terminalError: undefined,
            provisioningStatus: 'reconciling',
          });
        } else {
          return { outcome: 'requeue', delayMs: breaker.remainingCooldownMs() };
        }
      }

      if (tenant.desiredGeneration !== tenant.observedGeneration) {
        await this.repository.recordObservation(tenantId, {
          provisioningStatus: 'reconciling',
          failureCount: 0,
          lastErrorCode: undefined,
        });
      }

      const plan = calculatePlan(tenant);

      if (plan.isComplete) {
        await this.repository.markReady(tenantId, tenant.desiredGeneration);
        const breaker = this.getCircuitBreaker(tenantId);
        breaker.reset();
        return { outcome: 'complete', delayMs: 0 };
      }

      if (!plan.nextAction) {
        return { outcome: 'complete', delayMs: 0 };
      }

      const startTime = Date.now();
      try {
        const result = await this.executor.execute(plan.nextAction);
        const durationMs = Date.now() - startTime;

        const updates: Record<string, unknown> = {
          provisioningStatus: 'reconciling',
          lastReconciledAt: new Date(),
          failureCount: 0,
          lastErrorCode: undefined,
          terminalError: undefined,
          nextReconcileAt: new Date(Date.now() + calculateBackoff(0)),
        };

        if (plan.nextAction.type === 'create_identity' && result.externalResourceId) {
          updates.identityExternalId = result.externalResourceId;
        } else if (plan.nextAction.type === 'create_billing' && result.externalResourceId) {
          updates.billingExternalId = result.externalResourceId;
        } else if (plan.nextAction.type === 'create_database' && result.externalResourceId) {
          updates.databaseSchema = result.externalResourceId;
        } else if (plan.nextAction.type === 'create_dns' && result.externalResourceId) {
          updates.dnsRecordId = result.externalResourceId;
        }

        await this.repository.tryUpdateStatus(tenantId, updates, tenant.desiredGeneration);
        await this.repository.insertAuditLog({
          tenantId,
          generation: tenant.desiredGeneration,
          action: plan.nextAction.type,
          provider: plan.nextAction.provider,
          idempotencyKey: plan.nextAction.idempotencyKey,
          externalResourceId: result.externalResourceId,
          outcome: 'success',
          durationMs,
        });

        logger.info({ tenantId, action: plan.nextAction.type, durationMs, outcome: 'success' });
        return { outcome: 'requeue', delayMs: calculateBackoff(0) };
      } catch (error) {
        const durationMs = Date.now() - startTime;
        const err = error as Error;

        if (err instanceof TerminalError) {
          await this.repository.recordObservation(tenantId, {
            provisioningStatus: 'failed',
            failureCount: tenant.failureCount + 1,
            lastErrorCode: 'terminal_error',
            terminalError: err.userAction,
          });
          await this.repository.insertAuditLog({
            tenantId,
            generation: tenant.desiredGeneration,
            action: plan.nextAction!.type,
            provider: plan.nextAction!.provider,
            idempotencyKey: plan.nextAction!.idempotencyKey,
            outcome: 'terminal_error',
            errorCode: 'terminal_error',
            errorMessage: err.message,
            durationMs,
          });
          logger.warn({ tenantId, action: plan.nextAction!.type, error: err.message, userAction: err.userAction });
          return { outcome: 'requeue', delayMs: calculateBackoff(tenant.failureCount + 1) };
        }

        if (err instanceof RetryableError) {
          await this.repository.recordObservation(tenantId, {
            provisioningStatus: 'reconciling',
            failureCount: tenant.failureCount + 1,
            lastErrorCode: 'retryable',
          });
          await this.repository.insertAuditLog({
            tenantId,
            generation: tenant.desiredGeneration,
            action: plan.nextAction!.type,
            provider: plan.nextAction!.provider,
            idempotencyKey: plan.nextAction!.idempotencyKey,
            outcome: 'retryable_error',
            errorCode: 'retryable',
            errorMessage: err.message,
            durationMs,
          });
          logger.error({ tenantId, action: plan.nextAction!.type, error: err.message, attempt: tenant.failureCount + 1 });
          return { outcome: 'requeue', delayMs: calculateBackoff(tenant.failureCount + 1) };
        }

        await this.repository.recordObservation(tenantId, {
          provisioningStatus: 'reconciling',
          failureCount: tenant.failureCount + 1,
          lastErrorCode: 'unknown',
        });
        return { outcome: 'requeue', delayMs: calculateBackoff(tenant.failureCount + 1) };
      }
    } finally {
      this.lock.release(tenantId);
    }
  }

  private async processDeletion(tenant: TenantRow): Promise<ReconcileOutcome> {
    const plan = calculateDeletionPlan(tenant);

    if (plan.isComplete) {
      await this.repository.deleteTenant(tenant.tenantId);
      return { outcome: 'complete', delayMs: 0 };
    }

    if (!plan.nextAction) {
      await this.repository.markReady(tenant.tenantId, tenant.desiredGeneration);
      return { outcome: 'complete', delayMs: 0 };
    }

    try {
      const result = await this.executor.execute(plan.nextAction);
      if (result.success) {
        const updates: Record<string, unknown> = {};
        if (plan.nextAction.type === 'delete_dns') updates.dnsRecordId = null;
        if (plan.nextAction.type === 'delete_database') updates.databaseSchema = null;
        if (plan.nextAction.type === 'delete_billing') updates.billingExternalId = null;
        if (plan.nextAction.type === 'delete_identity') updates.identityExternalId = null;
        await this.repository.recordObservation(tenant.tenantId, updates);
      }
      return { outcome: 'requeue', delayMs: 1000 };
    } catch (error) {
      return { outcome: 'requeue', delayMs: calculateBackoff(tenant.failureCount) };
    }
  }

  private getCircuitBreaker(tenantId: string): CircuitBreaker {
    if (!this.circuitBreakers.has(tenantId)) {
      this.circuitBreakers.set(tenantId, new CircuitBreaker(5, 60000));
    }
    return this.circuitBreakers.get(tenantId)!;
  }
}