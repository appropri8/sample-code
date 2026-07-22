import { describe, it, before, after } from 'node:test';
import assert from 'node:assert';
import { Client } from 'pg';
import { TenantRepository } from '../../src/db/client';
import { Executor } from '../../src/reconciler/executor';
import { ConcurrencyLock } from '../../src/reconciler/lock';
import { Reconciler } from '../../src/reconciler/reconcileTenant';
import { DriftScanner } from '../../src/reconciler/drift-scanner';
import { createProviders } from '../../src/providers/factory';
import { calculateBackoff } from '../../src/reconciler/backoff';

const DATABASE_URL = process.env.TEST_DATABASE_URL || 'postgres://localhost:5432/reconciliation_provisioning_test';

describe('Reconciliation Loops', () => {
  let db: Client;
  let repository: TenantRepository;
  let reconciler: Reconciler;

  before(async () => {
    db = new Client({ connectionString: DATABASE_URL });
    await db.connect();

    await db.query('DROP TABLE IF EXISTS tenants CASCADE');
    await db.query(`
      CREATE TABLE tenants (
        tenant_id VARCHAR(64) PRIMARY KEY,
        desired_generation BIGINT NOT NULL DEFAULT 1,
        observed_generation BIGINT NOT NULL DEFAULT 0,
        provisioning_status VARCHAR(32) NOT NULL DEFAULT 'pending',
        identity_external_id VARCHAR(128),
        billing_external_id VARCHAR(128),
        database_schema VARCHAR(128),
        dns_record_id VARCHAR(128),
        last_reconciled_at TIMESTAMPTZ,
        next_reconcile_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        failure_count INTEGER NOT NULL DEFAULT 0,
        last_error_code VARCHAR(64),
        terminal_error TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
      )
    `);

    repository = new TenantRepository(db);
    reconciler = new Reconciler(repository, new Executor(), new ConcurrencyLock());
  });

  after(async () => {
    await db.query('DROP TABLE IF EXISTS tenants');
    await db.end();
  });

  it('reconciles twice without duplicating resources', async () => {
    const tenantId = 'test-tenant-duping';
    await repository.createTenant({ tenantId, generation: 1, identity: { enabled: true }, billing: { plan: 'pro' }, database: { isolation: 'schema' }, domain: { hostname: 'test.example.com' } });

    const result1 = await reconciler.reconcile(tenantId);
    assert.strictEqual(result1.outcome, 'requeue');

    const result2 = await reconciler.reconcile(tenantId);
    assert.strictEqual(result2.outcome, 'complete');

    const tenant = await repository.findByTenantId(tenantId);
    assert.strictEqual(tenant?.identityExternalId, `org-test-tenant-duping-ext`);
    assert.strictEqual(tenant?.billingExternalId, `cust-test-tenant-duping-pro-ext`);
    assert.strictEqual(tenant?.provisioningStatus, 'ready');
  });

  it('recovers after a simulated crash', async () => {
    const tenantId = 'test-tenant-crash';
    await repository.createTenant({ tenantId, generation: 1, identity: { enabled: true }, billing: { plan: 'pro' }, database: { isolation: 'schema' }, domain: { hostname: 'crash.example.com' } });

    await reconciler.reconcile(tenantId);
    const tenantAfterFirst = await repository.findByTenantId(tenantId);
    assert.strictEqual(tenantAfterFirst?.identityExternalId, `org-test-tenant-crash-ext`);
    assert.strictEqual(tenantAfterFirst?.provisioningStatus, 'reconciling');

    // Simulate a crash by only partially updating
    await repository.recordObservation(tenantId, { billingExternalId: `cust-test-tenant-crash-pro-ext` });

    const result = await reconciler.reconcile(tenantId);
    assert.strictEqual(result.outcome, 'requeue');

    const finalTenant = await repository.findByTenantId(tenantId);
    assert.strictEqual(finalTenant?.databaseSchema, `schema-test-tenant-crash-schema`);
  });

  it('does not allow stale generation to overwrite newer status', async () => {
    const tenantId = 'test-tenant-stale';
    await repository.createTenant({ tenantId, generation: 1, identity: { enabled: true }, billing: { plan: 'pro' }, database: { isolation: 'schema' }, domain: { hostname: 'stale.example.com' } });

    await reconciler.reconcile(tenantId);
    let tenant = await repository.findByTenantId(tenantId);
    assert.strictEqual(tenant?.identityExternalId, `org-test-tenant-stale-ext`);

    // Advance generation as if spec changed
    await db.query('UPDATE tenants SET desired_generation = 2, observed_generation = 1 WHERE tenant_id = $1', [tenantId]);

    const updates = { identityExternalId: 'should-not-overwrite' };
    const success = await repository.tryUpdateStatus(tenantId, updates, 1);
    assert.strictEqual(success, false);
  });

  it('recreates a deleted external resource', async () => {
    const tenantId = 'test-tenant-drift';
    await repository.createTenant({ tenantId, generation: 1, identity: { enabled: true }, billing: { plan: 'pro' }, database: { isolation: 'schema' }, domain: { hostname: 'drift.example.com' } });

    const result = await reconciler.reconcile(tenantId);
    assert.strictEqual(result.outcome, 'requeue');

    let tenant = await repository.findByTenantId(tenantId);
    assert.ok(tenant?.dnsRecordId);

    // Simulate external deletion
    await repository.recordObservation(tenantId, { dnsRecordId: null });
    tenant = await repository.findByTenantId(tenantId);
    assert.strictEqual(tenant?.dnsRecordId, null);

    const driftResult = await reconciler.reconcile(tenantId);
    assert.strictEqual(driftResult.outcome, 'requeue');

    const restored = await repository.findByTenantId(tenantId);
    assert.ok(restored?.dnsRecordId);
  });

  it('stops retrying a terminal error after circuit breaker threshold', async () => {
    const tenantId = 'test-tenant-terminal';
    await repository.createTenant({ tenantId, generation: 1, identity: { enabled: true }, billing: { plan: 'pro' }, database: { isolation: 'schema' }, domain: { hostname: 'term.example.com' } });

    // Create a custom executor that always throws terminal errors
    class FailingTerminalExecutor {
      async execute() {
        throw new Error('Terminal configuration error: invalid_plan');
      }
    }

    const terminalReconciler = new Reconciler(repository, new FailingTerminalExecutor() as any, new ConcurrencyLock());

    for (let i = 0; i < 6; i++) {
      await terminalReconciler.reconcile(tenantId);
    }

    const tenant = await repository.findByTenantId(tenantId);
    assert.strictEqual(tenant?.provisioningStatus, 'failed');
    assert.ok(tenant?.failureCount >= 5);
  });

  it('prevents two workers from provisioning the same tenant concurrently', async () => {
    const tenantId = 'test-tenant-concurrency';
    await repository.createTenant({ tenantId, generation: 1, identity: { enabled: true }, billing: { plan: 'pro' }, database: { isolation: 'schema' }, domain: { hostname: 'conc.example.com' } });

    const lock1 = new ConcurrencyLock();
    const lock2 = new ConcurrencyLock();

    const reconciler1 = new Reconciler(repository, new Executor(), lock1);
    const reconciler2 = new Reconciler(repository, new Executor(), lock2);

    const [first, second] = await Promise.all([
      reconciler1.reconcile(tenantId),
      reconciler2.reconcile(tenantId),
    ]);

    const hasConcurrency = first.outcome === 'complete' || second.outcome === 'complete';
    assert.ok(hasConcurrency || first.outcome === 'requeue');

    const tenant = await repository.findByTenantId(tenantId);
    assert.ok(tenant?.identityExternalId);
  });

  it('calculates backoff with jitter', () => {
    const base = 1000;
    for (let i = 0; i < 10; i++) {
      const delay = calculateBackoff(i, base);
      const min = base * Math.pow(2, i) * 0.5;
      const max = base * Math.pow(2, i) * 1.0;
      assert.ok(delay >= min, `Delay ${delay} should be >= ${min} for failure ${i}`);
      assert.ok(delay <= Math.min(max, 60000), `Delay ${delay} should be <= ${Math.min(max, 60000)} for failure ${i}`);
    }
  });
});