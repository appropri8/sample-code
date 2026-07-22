import { Client } from 'pg';
import { TenantRepository } from './db/client';
import { Executor } from './reconciler/executor';
import { ConcurrencyLock } from './reconciler/lock';
import { Reconciler } from './reconciler/reconcileTenant';
import { DriftScanner } from './reconciler/drift-scanner';
import { logger } from './utils/logging';

const DATABASE_URL = process.env.DATABASE_URL || 'postgres://localhost:5432/reconciliation_provisioning';

async function main(): Promise<void> {
  const db = new Client({ connectionString: DATABASE_URL });
  await db.connect();

  const repository = new TenantRepository(db);
  const executor = new Executor();
  const lock = new ConcurrencyLock();
  const reconciler = new Reconciler(repository, executor, lock);
  const driftScanner = new DriftScanner(repository, executor, lock, 10);

  logger.info('Reconciliation system starting');

  // Run reconciliation loop
  const reconcilerLoop = setInterval(async () => {
    try {
      const tenants = await repository.findTenantsNeedingReconciliation(5);
      for (const tenant of tenants) {
        const result = await reconciler.reconcile(tenant.tenantId);
        logger.info({ tenantId: tenant.tenantId, outcome: result.outcome, delayMs: result.delayMs });
      }
    } catch (error) {
      logger.error({ error }, 'Reconciliation loop failed');
    }
  }, 2000);

  // Run drift scanner every 10 seconds
  const driftLoop = setInterval(async () => {
    try {
      await driftScanner.scan();
    } catch (error) {
      logger.error({ error }, 'Drift scanner failed');
    }
  }, 10000);

  // Graceful shutdown
  process.on('SIGTERM', () => {
    clearInterval(reconcilerLoop);
    clearInterval(driftLoop);
    db.end();
    logger.info('Reconciliation system stopped');
    process.exit(0);
  });
}

main().catch((error) => {
  logger.error({ error }, 'Fatal error');
  process.exit(1);
});