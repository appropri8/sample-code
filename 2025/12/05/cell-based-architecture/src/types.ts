export interface Cell {
  id: string;
  region: string;
  status: 'active' | 'draining' | 'inactive';
  capacity: {
    maxTenants: number;
    currentTenants: number;
  };
  endpoints: {
    api: string;
    metrics: string;
  };
  createdAt: Date;
  updatedAt: Date;
}

export interface Tenant {
  id: string;
  cellId: string;
  name: string;
  tier: 'free' | 'paid' | 'enterprise';
  region?: string;
  migratedAt: Date;
}

export interface RoutingRule {
  id: string;
  version: number;
  tenantId?: string;
  region?: string;
  segment?: string;
  cellId: string;
  priority: number;
  active: boolean;
}

export interface CellContext {
  tenantId: string;
  cellId: string;
  region?: string;
}

export interface TenantMapping {
  tenantId: string;
  cellId: string;
}

export interface RoutingResponse {
  mappings: TenantMapping[];
  version: number;
  updatedAt: string;
}
