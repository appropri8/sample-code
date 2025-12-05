import { TenantMapping, RoutingResponse } from './types';

export interface CellRouter {
  getCellForTenant(tenantId: string): Promise<string | null>;
  refresh(): Promise<void>;
  stop(): void;
}

export class InMemoryCellRouter implements CellRouter {
  private tenantToCell: Map<string, string> = new Map();
  private controlPlaneUrl: string;
  private refreshInterval: number = 5 * 60 * 1000; // 5 minutes
  private refreshTimer?: NodeJS.Timeout;

  constructor(controlPlaneUrl: string) {
    this.controlPlaneUrl = controlPlaneUrl;
    this.startRefresh();
  }

  async getCellForTenant(tenantId: string): Promise<string | null> {
    // Check cache first
    const cellId = this.tenantToCell.get(tenantId);
    if (cellId) {
      return cellId;
    }

    // If not in cache, fetch from control plane
    await this.refresh();
    return this.tenantToCell.get(tenantId) || null;
  }

  async refresh(): Promise<void> {
    try {
      const response = await fetch(`${this.controlPlaneUrl}/api/routing/tenants`);
      if (!response.ok) {
        throw new Error(`Control plane returned ${response.status}`);
      }
      
      const data: RoutingResponse = await response.json();
      
      // Update in-memory map
      this.tenantToCell.clear();
      for (const mapping of data.mappings) {
        this.tenantToCell.set(mapping.tenantId, mapping.cellId);
      }
      
      console.log(`Refreshed routing table: ${this.tenantToCell.size} tenant mappings`);
    } catch (error) {
      console.error('Failed to refresh routing table:', error);
      // Keep existing mappings on error
    }
  }

  private startRefresh(): void {
    // Initial refresh
    this.refresh();

    // Periodic refresh
    this.refreshTimer = setInterval(() => {
      this.refresh();
    }, this.refreshInterval);
  }

  stop(): void {
    if (this.refreshTimer) {
      clearInterval(this.refreshTimer);
    }
  }

  // For testing/debugging
  getCacheSize(): number {
    return this.tenantToCell.size;
  }
}
