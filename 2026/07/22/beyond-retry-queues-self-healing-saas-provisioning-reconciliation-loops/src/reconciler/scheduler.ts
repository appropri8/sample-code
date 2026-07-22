import { TenantRepository } from '../db/client';
import { Reconciler } from './reconcileTenant';
import { ConcurrencyLock } from './lock';
import { DriftScanner } from './drift-scanner';
import { logger } from '../utils/logging';

export class ReconciliationLoop {
  private running = false;
  private reconciler: Reconciler;
  private driftScanner: DriftScanner;

  constructor(
    private readonly repository: TenantRepository,
    private readonly executor: any,
    private readonly lock: ConcurrencyLock,
    private readonly batchSize: number = 10
  ) {
    this.reconciler = new Reconciler(repository, executor, lock);
    this.driftScanner = new DriftScanner(repository, executor, lock, batchSize);
  }

  start(): void {
    if (this.running) return;
    this.running = true;
    this.tick();
  }

  stop(): void {
    this.running = false;
  }

  private async tick(): Promise<void> {
    if (!this.running) return;

    try {
      await this.runReconciliation();
      await this.runDriftScan();
    } catch (error) {
      logger.error({ error }, 'Reconciliation tick failed');
    }

    setTimeout(() => this.tick(), 2000);
  }

  private async runReconciliation(): Promise<void> {
    const tenants = await this.repository.findTenantsNeedingReconciliation(this.batchSize);
    for (const tenant of tenants) {
      const result = await this.reconciler.reconcile(tenant.tenantId);
      logger.info({ tenantId: tenant.tenantId, outcome: result.outcome, delayMs: result.delayMs });
    }
  }

  private async runDriftScan(): Promise<void> {
    await this.driftScanner.scan();
  }
}