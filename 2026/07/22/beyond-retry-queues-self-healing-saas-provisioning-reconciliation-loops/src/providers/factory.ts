import { ProvisioningAction, ProvisioningResult } from './interfaces';
import { DnsProviderAdapter } from './dns-provider';

export class MockIdentityProvider implements {
  name = 'identity';
  async execute(action: ProvisioningAction): Promise<ProvisioningResult> {
    if (action.type === 'create_identity') {
      const { tenantId } = action.input as { tenantId: string };
      return {
        success: true,
        externalResourceId: `org-${tenantId}-ext`,
      };
    }
    return { success: false, error: 'unknown action' };
  }
}

export class MockBillingProvider implements {
  name = 'billing';
  async execute(action: ProvisioningAction): Promise<ProvisioningResult> {
    if (action.type === 'create_billing') {
      const { plan, tenantId } = action.input as { plan: string; tenantId: string };
      return {
        success: true,
        externalResourceId: `cust-${tenantId}-${plan}-ext`,
      };
    }
    return { success: false, error: 'unknown action' };
  }
}

export class MockDatabaseProvider implements {
  name = 'database';
  async execute(action: ProvisioningAction): Promise<ProvisioningResult> {
    if (action.type === 'create_database') {
      const { tenantId, isolation } = action.input as { tenantId: string; isolation: string };
      return {
        success: true,
        externalResourceId: `schema-${tenantId}-${isolation}`,
      };
    }
    return { success: false, error: 'unknown action' };
  }
}

export function createProviders() {
  return {
    identity: new MockIdentityProvider(),
    billing: new MockBillingProvider(),
    database: new MockDatabaseProvider(),
    dns: new DnsProviderAdapter() as any,
  };
}