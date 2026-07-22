import { TenantRow } from '../models/tenant';
import { ProvisioningAction } from '../providers/interfaces';

export interface Plan {
  isComplete: boolean;
  nextAction?: ProvisioningAction;
}

export function calculatePlan(tenant: TenantRow): Plan {
  const actions: ProvisioningAction[] = [];

  if (!tenant.identityExternalId) {
    actions.push({
      type: 'create_identity',
      provider: 'identity',
      idempotencyKey: `${tenant.tenantId}:${tenant.desiredGeneration}:identity`,
      input: { tenantId: tenant.tenantId },
    });
  }

  if (!tenant.billingExternalId) {
    actions.push({
      type: 'create_billing',
      provider: 'billing',
      idempotencyKey: `${tenant.tenantId}:${tenant.desiredGeneration}:billing`,
      input: { tenantId: tenant.tenantId, plan: 'pro' },
    });
  }

  if (!tenant.databaseSchema) {
    actions.push({
      type: 'create_database',
      provider: 'database',
      idempotencyKey: `${tenant.tenantId}:${tenant.desiredGeneration}:database`,
      input: { tenantId: tenant.tenantId, isolation: 'schema' },
    });
  }

  if (!tenant.dnsRecordId) {
    actions.push({
      type: 'create_dns',
      provider: 'dns',
      idempotencyKey: `${tenant.tenantId}:${tenant.desiredGeneration}:dns`,
      input: { tenantId: tenant.tenantId, hostname: `${tenant.tenantId}.example.com` },
    });
  }

  return {
    isComplete: actions.length === 0,
    nextAction: actions[0],
  };
}

export function calculateDeletionPlan(tenant: TenantRow): Plan {
  const actions: ProvisioningAction[] = [];

  if (tenant.dnsRecordId) {
    actions.push({
      type: 'delete_dns',
      provider: 'dns',
      idempotencyKey: `delete-${tenant.tenantId}:dns`,
      input: { recordId: tenant.dnsRecordId },
    });
  }

  if (tenant.databaseSchema) {
    actions.push({
      type: 'delete_database',
      provider: 'database',
      idempotencyKey: `delete-${tenant.tenantId}:database`,
      input: { schema: tenant.databaseSchema },
    });
  }

  if (tenant.billingExternalId) {
    actions.push({
      type: 'delete_billing',
      provider: 'billing',
      idempotencyKey: `delete-${tenant.tenantId}:billing`,
      input: { customerId: tenant.billingExternalId },
    });
  }

  if (tenant.identityExternalId) {
    actions.push({
      type: 'delete_identity',
      provider: 'identity',
      idempotencyKey: `delete-${tenant.tenantId}:identity`,
      input: { orgId: tenant.identityExternalId },
    });
  }

  return {
    isComplete: actions.length === 0,
    nextAction: actions[0],
  };
}