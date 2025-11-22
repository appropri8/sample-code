import { ControlPlaneAPI } from './control-plane';
import { CellDirectory } from './cell-directory';

export interface DataMigrator {
  migrateTenantData(
    tenantId: string,
    sourceCell: string,
    targetCell: string
  ): Promise<void>;
  getRecordCount(tenantId: string, cellId: string): Promise<number>;
  getSampleRecords(tenantId: string, cellId: string, count: number): Promise<any[]>;
  getRecord(recordId: string, cellId: string): Promise<any>;
  recordsMatch(record1: any, record2: any): boolean;
  getActiveRequestCount(tenantId: string, cellId: string): Promise<number>;
}

class SimpleDataMigrator implements DataMigrator {
  async migrateTenantData(
    tenantId: string,
    sourceCell: string,
    targetCell: string
  ): Promise<void> {
    // In real implementation, this would:
    // - Connect to source database
    // - Connect to target database
    // - Copy all tenant data
    // - Verify data integrity
    console.log(`Migrating tenant ${tenantId} from ${sourceCell} to ${targetCell}`);
    
    // Simulate migration delay
    await new Promise(resolve => setTimeout(resolve, 100));
  }

  async getRecordCount(tenantId: string, cellId: string): Promise<number> {
    // In real implementation, query database
    return 100; // Mock value
  }

  async getSampleRecords(tenantId: string, cellId: string, count: number): Promise<any[]> {
    // In real implementation, query database
    return Array.from({ length: count }, (_, i) => ({
      id: `record-${i}`,
      tenantId,
      data: `sample-data-${i}`
    }));
  }

  async getRecord(recordId: string, cellId: string): Promise<any> {
    // In real implementation, query database
    return {
      id: recordId,
      data: `data-for-${recordId}`
    };
  }

  recordsMatch(record1: any, record2: any): boolean {
    return JSON.stringify(record1) === JSON.stringify(record2);
  }

  async getActiveRequestCount(tenantId: string, cellId: string): Promise<number> {
    // In real implementation, check active requests
    return 0; // Mock value
  }
}

export class TenantRebalancer {
  private controlPlane: ControlPlaneAPI;
  private directory: CellDirectory;
  private dataMigrator: DataMigrator;

  constructor(
    controlPlane: ControlPlaneAPI,
    directory: CellDirectory,
    dataMigrator?: DataMigrator
  ) {
    this.controlPlane = controlPlane;
    this.directory = directory;
    this.dataMigrator = dataMigrator || new SimpleDataMigrator();
  }

  async rebalanceTenant(tenantId: string, targetCellId: string): Promise<void> {
    // Step 1: Mark tenant as moving
    await this.controlPlane.markTenantMoving(tenantId);

    // Step 2: Get current cell
    const currentCellId = await this.controlPlane.getCellForTenant(tenantId);
    if (!currentCellId) {
      throw new Error('Tenant not found in any cell');
    }

    if (currentCellId === targetCellId) {
      throw new Error('Tenant already in target cell');
    }

    // Step 3: Backfill data to target cell
    await this.dataMigrator.migrateTenantData(tenantId, currentCellId, targetCellId);

    // Step 4: Verify data integrity
    const verified = await this.verifyDataIntegrity(tenantId, currentCellId, targetCellId);
    if (!verified) {
      throw new Error('Data integrity check failed');
    }

    // Step 5: Flip routing
    await this.controlPlane.assignTenantToCell(tenantId, targetCellId);
    this.directory.invalidateCache(tenantId);

    // Step 6: Wait for traffic to drain from old cell
    await this.waitForTrafficDrain(tenantId, currentCellId);

    // Step 7: Clean up old cell data (optional, can be delayed)
    // await this.dataMigrator.cleanupOldData(tenantId, currentCellId);
  }

  private async verifyDataIntegrity(
    tenantId: string,
    sourceCell: string,
    targetCell: string
  ): Promise<boolean> {
    // Compare record counts
    const sourceCount = await this.dataMigrator.getRecordCount(tenantId, sourceCell);
    const targetCount = await this.dataMigrator.getRecordCount(tenantId, targetCell);

    if (sourceCount !== targetCount) {
      console.error('Record count mismatch', { sourceCount, targetCount });
      return false;
    }

    // Sample records and compare
    const sample = await this.dataMigrator.getSampleRecords(tenantId, sourceCell, 10);
    for (const record of sample) {
      const targetRecord = await this.dataMigrator.getRecord(record.id, targetCell);
      if (!this.dataMigrator.recordsMatch(record, targetRecord)) {
        console.error('Record mismatch', { recordId: record.id });
        return false;
      }
    }

    return true;
  }

  private async waitForTrafficDrain(tenantId: string, cellId: string): Promise<void> {
    // Wait until no active requests for this tenant in the old cell
    let attempts = 0;
    while (attempts < 60) {
      const activeRequests = await this.dataMigrator.getActiveRequestCount(tenantId, cellId);
      if (activeRequests === 0) {
        return;
      }
      await new Promise(resolve => setTimeout(resolve, 1000));
      attempts++;
    }

    throw new Error('Traffic drain timeout');
  }
}


