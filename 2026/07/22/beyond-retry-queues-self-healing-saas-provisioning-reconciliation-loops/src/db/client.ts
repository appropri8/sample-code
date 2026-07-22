import { Client } from 'pg';
import { TenantRow, TenantStatus } from '../models/tenant';

export class TenantRepository {
  constructor(private readonly db: Client) {}

  async findTenantsNeedingReconciliation(batchSize: number): Promise<TenantRow[]> {
    const result = await this.db.query<TenantRow>(
      `SELECT * FROM tenants
       WHERE next_reconcile_at <= NOW()
         AND provisioning_status NOT IN ('deleted', 'deleting')
       ORDER BY next_reconcile_at ASC
       LIMIT $1
       FOR UPDATE SKIP LOCKED`,
      [batchSize]
    );
    return result.rows;
  }

  async findByTenantId(tenantId: string): Promise<TenantRow | null> {
    const result = await this.db.query<TenantRow>(
      'SELECT * FROM tenants WHERE tenant_id = $1',
      [tenantId]
    );
    return result.rows[0] ?? null;
  }

  async lockTenant(tenantId: string): Promise<TenantRow | null> {
    const result = await this.db.query<TenantRow>(
      `SELECT * FROM tenants
       WHERE tenant_id = $1
       AND provisioning_status NOT IN ('deleted', 'deleting')
       FOR UPDATE`,
      [tenantId]
    );
    return result.rows[0] ?? null;
  }

  async lockTenantsForDriftScan(batchSize: number): Promise<TenantRow[]> {
    const result = await this.db.query<TenantRow>(
      `SELECT * FROM tenants
       WHERE provisioning_status = 'ready'
       ORDER BY next_reconcile_at ASC
       LIMIT $1
       FOR UPDATE SKIP LOCKED`,
      [batchSize]
    );
    return result.rows;
  }

  async createTenant(spec: import('../models/tenant').TenantSpec): Promise<TenantRow> {
    const result = await this.db.query<TenantRow>(
      `INSERT INTO tenants (tenant_id, desired_generation, provisioning_status, next_reconcile_at)
       VALUES ($1, $2, 'pending', NOW())
       RETURNING *`,
      [spec.tenantId, spec.generation]
    );
    return result.rows[0];
  }

  async markReady(tenantId: string, generation: number): Promise<void> {
    await this.db.query(
      `UPDATE tenants
       SET provisioning_status = 'ready',
           observed_generation = $2,
           failure_count = 0,
           last_error_code = NULL,
           terminal_error = NULL,
           next_reconcile_at = NOW() + INTERVAL '1 hour',
           updated_at = NOW()
       WHERE tenant_id = $1`,
      [tenantId, generation]
    );
  }

  async recordObservation(tenantId: string, status: Partial<TenantStatus>): Promise<void> {
    const sets: string[] = [];
    const values: unknown[] = [tenantId];
    let idx = 2;

    for (const [key, value] of Object.entries(status)) {
      if (value === undefined) continue;
      const column = key.replace(/([A-Z])/g, '_$1').toLowerCase();
      sets.push(`${column} = $${idx}`);
      values.push(value);
      idx++;
    }

    sets.push(`updated_at = NOW()`);

    await this.db.query(
      `UPDATE tenants SET ${sets.join(', ')} WHERE tenant_id = $1`,
      values
    );
  }

  async tryUpdateStatus(
    tenantId: string,
    status: Partial<TenantStatus>,
    expectedGeneration: number
  ): Promise<boolean> {
    const result = await this.db.query(
      `UPDATE tenants
       SET provisioning_status = COALESCE($2, provisioning_status),
           observed_generation = $3,
           failure_count = COALESCE($4, failure_count),
           last_error_code = COALESCE($5, last_error_code),
           terminal_error = COALESCE($6, terminal_error),
           next_reconcile_at = COALESCE($7, next_reconcile_at),
           updated_at = NOW()
       WHERE tenant_id = $8
         AND desired_generation = $9
       RETURNING tenant_id`,
      [
        status.provisioningStatus,
        status.observedGeneration ?? 'observed_generation',
        status.failureCount,
        status.lastErrorCode,
        status.terminalError,
        status.nextReconcileAt,
        tenantId,
        expectedGeneration,
      ]
    );

    return result.rows.length > 0;
  }

  async deleteTenant(tenantId: string): Promise<void> {
    await this.db.query('DELETE FROM tenants WHERE tenant_id = $1', [tenantId]);
  }

  async insertIdempotencyKey(
    key: string,
    tenantId: string,
    provider: string,
    externalResourceId: string
  ): Promise<void> {
    await this.db.query(
      `INSERT INTO idempotency_keys (key, tenant_id, provider, external_resource_id)
       VALUES ($1, $2, $3, $4)
       ON CONFLICT (key) DO NOTHING`,
      [key, tenantId, provider, externalResourceId]
    );
  }

  async findIdempotencyKey(key: string): Promise<{ tenantId: string; provider: string; externalResourceId: string } | null> {
    const result = await this.db.query(
      'SELECT tenant_id, provider, external_resource_id FROM idempotency_keys WHERE key = $1',
      [key]
    );
    return result.rows[0] ?? null;
  }

  async insertAuditLog(entry: {
    tenantId: string;
    generation: number;
    action: string;
    provider: string;
    idempotencyKey: string;
    externalResourceId?: string;
    outcome: string;
    errorCode?: string;
    errorMessage?: string;
    durationMs?: number;
  }): Promise<void> {
    await this.db.query(
      `INSERT INTO audit_log
       (tenant_id, generation, action, provider, idempotency_key, external_resource_id, outcome, error_code, error_message, duration_ms)
       VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)`,
      [
        entry.tenantId,
        entry.generation,
        entry.action,
        entry.provider,
        entry.idempotencyKey,
        entry.externalResourceId ?? null,
        entry.outcome,
        entry.errorCode ?? null,
        entry.errorMessage ?? null,
        entry.durationMs ?? null,
      ]
    );
  }
}