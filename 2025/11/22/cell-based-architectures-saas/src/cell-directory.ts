export interface TenantInfo {
  id: string;
  tier: string;
  createdAt: Date;
}

export interface ControlPlaneClient {
  getTenant(tenantId: string): Promise<TenantInfo>;
}

interface CachedCell {
  cell: string;
  expires: number;
}

export class CellDirectory {
  private cache: Map<string, CachedCell>;
  private controlPlane: ControlPlaneClient;
  private ttl: number;

  constructor(controlPlane: ControlPlaneClient, ttl: number = 300000) {
    this.cache = new Map();
    this.controlPlane = controlPlane;
    this.ttl = ttl; // 5 minutes default
  }

  async getCellForTenant(tenantId: string): Promise<string> {
    // Check cache first
    const cached = this.cache.get(tenantId);
    if (cached && cached.expires > Date.now()) {
      return cached.cell;
    }

    // Get tenant info from control plane
    const tenant = await this.controlPlane.getTenant(tenantId);

    // Determine cell based on tenant info
    const cell = this.determineCell(tenant);

    // Cache result
    this.cache.set(tenantId, {
      cell,
      expires: Date.now() + this.ttl
    });

    return cell;
  }

  private determineCell(tenant: TenantInfo): string {
    // VIP tenants get dedicated cells
    if (tenant.tier === 'vip') {
      return `cell-vip-${this.hashString(tenant.id) % 10}`;
    }

    // Enterprise tenants get shared enterprise cells
    if (tenant.tier === 'enterprise') {
      return `cell-enterprise-${this.hashString(tenant.id) % 20}`;
    }

    // Regular tenants use hash-based routing to shared cells
    return `cell-shared-${this.hashString(tenant.id) % 100}`;
  }

  private hashString(str: string): number {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32-bit integer
    }
    return Math.abs(hash);
  }

  invalidateCache(tenantId: string): void {
    this.cache.delete(tenantId);
  }

  clearCache(): void {
    this.cache.clear();
  }
}


