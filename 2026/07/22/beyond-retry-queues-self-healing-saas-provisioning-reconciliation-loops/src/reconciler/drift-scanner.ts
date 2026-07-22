import { TenantRow } from '../models/tenant';
import { TenantRepository } from '../db/client';
import { Executor } from './executor';
import { calculatePlan } from './planner';
import { calculateBackoff } from './backoff';
import { RetryableError, TerminalError } from './errors';
import { ConcurrencyLock } from './lock';
import { logger } from '../utils/logging';

export class DriftScanner {
  constructor(
    private readonly repository: TenantRepository,
    private readonly executor: Executor,
    private readonly lock: ConcurrencyLock,
    private readonly batchSize: number = 10
  ) {}

  async scan(): Promise<void> {
    const tenants = await this.repository.lockTenantsForDriftScan(this.batchSize);
    for (const tenant of tenants) {
      const acquired = await this.lock.acquire(tenant.tenantId, 30000);
      if (!acquired) {
        continue;
      }

      try {
        await this.scanTenant(tenant);
      } catch (error) {
        logger.error({ tenantId: tenant.tenantId, error }, 'Drift scan failed');
      } finally {
        this.lock.release(tenant.tenantId);
      }
    }
  }

  private async scanTenant(tenant: TenantRow): Promise<void> {
    const plan = calculatePlan(tenant);

    if (plan.isComplete) {
      await this.repository.markReady(tenant.tenantId, tenant.desiredGeneration);
      return;
    }

    if (!plan.nextAction) {
      return;
    }

    try {
      const result = await this.executor.execute(plan.nextAction);
      const updates: Record<string, unknown> = {
        lastReconciledAt: new Date(),
        nextReconcileAt: new Date(Date.now() + calculateBackoff(0)),
        failureCount: 0,
        lastErrorCode: undefined,
        terminalError: undefined,
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

      await this.repository.tryUpdateStatus(tenant.tenantId, updates, tenant.desiredGeneration);
      logger.info({ tenantId: tenant.tenantId, action: plan.nextAction.type, drift: true });
    } catch (error) {
      const err = error as Error;
      await this.repository.recordObservation(tenant.tenantId, {
        failureCount: tenant.failureCount + 1,
        lastErrorCode: err instanceof RetryableError ? 'drift_retryable' : 'drift_unknown',
      });
      logger.warn({ tenantId: tenant.tenantId, action: plan.nextAction!.type, error: err.message });
    }
  }
}