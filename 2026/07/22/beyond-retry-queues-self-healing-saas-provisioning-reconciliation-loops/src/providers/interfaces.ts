export interface ProvisioningAction {
  type: 'create_identity' | 'create_billing' | 'create_database' | 'create_dns' | 'delete_identity' | 'delete_billing' | 'delete_database' | 'delete_dns';
  provider: string;
  idempotencyKey: string;
  input: Record<string, unknown>;
}

export interface ProvisioningResult {
  success: boolean;
  externalResourceId?: string;
  error?: string;
  errorCode?: string;
  alreadyExists?: boolean;
}

export interface ProviderAdapter {
  name: string;
  execute(action: ProvisioningAction): Promise<ProvisioningResult>;
}