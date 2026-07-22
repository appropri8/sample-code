CREATE TABLE IF NOT EXISTS tenants (
    tenant_id VARCHAR(64) PRIMARY KEY,
    desired_generation BIGINT NOT NULL DEFAULT 1,
    observed_generation BIGINT NOT NULL DEFAULT 0,
    provisioning_status VARCHAR(32) NOT NULL DEFAULT 'pending'
        CHECK (provisioning_status IN ('pending','reconciling','ready','degraded','failed','deleting','deleted')),
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
);

CREATE TABLE IF NOT EXISTS idempotency_keys (
    key VARCHAR(256) PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL,
    provider VARCHAR(64) NOT NULL,
    external_resource_id VARCHAR(128),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS audit_log (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL,
    generation BIGINT NOT NULL,
    action VARCHAR(64) NOT NULL,
    provider VARCHAR(64) NOT NULL,
    idempotency_key VARCHAR(256) NOT NULL,
    external_resource_id VARCHAR(128),
    outcome VARCHAR(32) NOT NULL,
    error_code VARCHAR(64),
    error_message TEXT,
    duration_ms INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tenants_next_reconcile ON tenants(next_reconcile_at);
CREATE INDEX IF NOT EXISTS idx_tenants_status ON tenants(provisioning_status);
CREATE INDEX IF NOT EXISTS idx_audit_log_tenant ON audit_log(tenant_id, created_at);