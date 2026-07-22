import { describe, it, before, after } from 'node:test';
import assert from 'node:assert';
import { Client } from 'pg';
import { TenantRepository } from '../../src/db/client';
import { DriftScanner } from '../../src/reconciler/drift-scanner';

const DATABASE_URL = process.env.TEST_DATABASE_URL || 'postgres://localhost:5432/reconciliation_provisioning_test';

describe('DriftScanner', () => {
  let db: Client;
  let repository: TenantRepository;
  let scanner: DriftScanner;

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
    scanner = new DriftScanner(repository, {
      async execute() {
        return { success: true, externalResourceId: 'drift-recreated-id' };
      },
    } as any, new (await import('../../src/reconciler/lock')).ConcurrencyLock(), 10);
  });

  after(async () => {
    await db.query('DROP TABLE IF EXISTS tenants');
    await db.end();
  });

  it('detects and repairs missing DNS records', async () => {
    const tenantId = 'drift-test-1';
    await db.query(
      `INSERT INTO tenants (tenant_id, desired_generation, observed_generation, provisioning_status, identity_external_id, billing_external_id, database_schema, dns_record_id)
       VALUES ($1, $2, $3, 'ready', $4, $5, $6, $7)`,
      [tenantId, 1, 1, 'org-ext', 'cust-ext', 'schema-ext', null]
    );

    await scanner.scan();

    const tenant = await repository.findByTenantId(tenantId);
    assert.strictEqual(tenant?.dnsRecordId, 'drift-recreated-id');
    assert.strictEqual(tenant?.provisioningStatus, 'ready');
  });

  it('does nothing when tenant is fully ready', async () => {
    const tenantId = 'drift-test-2';
    await db.query(
      `INSERT INTO tenants (tenant_id, desired_generation, observed_generation, provisioning_status, identity_external_id, billing_external_id, database_schema, dns_record_id)
       VALUES ($1, $2, $3, 'ready', $4, $5, $6, $7)`,
      [tenantId, 1, 1, 'org-ext', 'cust-ext', 'schema-ext', 'dns-ext']
    );

    await scanner.scan();

    const tenant = await repository.findByTenantId(tenantId);
    assert.strictEqual(tenant?.provisioningStatus, 'ready');
  });
});