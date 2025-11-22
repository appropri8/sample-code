import { CellDirectory } from '../src/cell-directory';
import { ControlPlaneAPI } from '../src/control-plane';

describe('CellDirectory', () => {
  let controlPlane: ControlPlaneAPI;
  let directory: CellDirectory;

  beforeEach(() => {
    controlPlane = new ControlPlaneAPI();
    directory = new CellDirectory(controlPlane);
  });

  test('should get cell for tenant', async () => {
    await controlPlane.setTenantTier('tenant-1', 'regular');
    await controlPlane.assignTenantToCell('tenant-1', 'cell-1');

    const cell = await directory.getCellForTenant('tenant-1');
    expect(cell).toBeDefined();
  });

  test('should cache cell mappings', async () => {
    await controlPlane.setTenantTier('tenant-1', 'regular');
    await controlPlane.assignTenantToCell('tenant-1', 'cell-1');

    const cell1 = await directory.getCellForTenant('tenant-1');
    const cell2 = await directory.getCellForTenant('tenant-1');

    expect(cell1).toBe(cell2);
  });

  test('should invalidate cache', async () => {
    await controlPlane.setTenantTier('tenant-1', 'regular');
    await controlPlane.assignTenantToCell('tenant-1', 'cell-1');

    await directory.getCellForTenant('tenant-1');
    directory.invalidateCache('tenant-1');

    // Cache should be cleared
    const cell = await directory.getCellForTenant('tenant-1');
    expect(cell).toBeDefined();
  });

  test('should route VIP tenants to dedicated cells', async () => {
    await controlPlane.setTenantTier('tenant-vip', 'vip');
    await controlPlane.assignTenantToCell('tenant-vip', 'cell-vip-1');

    const cell = await directory.getCellForTenant('tenant-vip');
    expect(cell).toContain('cell-vip');
  });

  test('should route enterprise tenants to enterprise cells', async () => {
    await controlPlane.setTenantTier('tenant-enterprise', 'enterprise');
    await controlPlane.assignTenantToCell('tenant-enterprise', 'cell-enterprise-1');

    const cell = await directory.getCellForTenant('tenant-enterprise');
    expect(cell).toContain('cell-enterprise');
  });
});


