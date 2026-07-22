export interface TenantSpec {
  tenantId: string;
  generation: number;
  identity: { enabled: boolean };
  billing: { plan: string };
  database: { isolation: string };
  domain: { hostname: string };
}

export type ProvisioningStatus =
  | 'pending'
  | 'reconciling'
  | 'ready'
  | 'degraded'
  | 'failed'
  | 'deleting'
  | 'deleted';

export interface TenantStatus {
  tenantId: string;
  desiredGeneration: number;
  observedGeneration: number;
  provisioningStatus: ProvisioningStatus;
  identityExternalId?: string;
  billingExternalId?: string;
  databaseSchema?: string;
  dnsRecordId?: string;
  lastReconciledAt?: Date;
  nextReconcileAt: Date;
  failureCount: number;
  lastErrorCode?: string;
  terminalError?: string;
}

export interface TenantRow extends TenantStatus {
  createdAt: Date;
  updatedAt: Date;
}

export interface ReconcileOutcome {
  outcome: 'complete' | 'requeue';
  delayMs: number;
}