import { ControlPlaneAPI } from '../src/control-plane';

describe('ControlPlaneAPI', () => {
  let controlPlane: ControlPlaneAPI;

  beforeEach(() => {
    controlPlane = new ControlPlaneAPI();
  });

  test('should create a cell', async () => {
    const cell = await controlPlane.createCell({
      id: 'cell-1',
      capacity: 100
    });

    expect(cell.id).toBe('cell-1');
    expect(cell.capacity).toBe(100);
    expect(cell.status).toBe('provisioning');
  });

  test('should not create duplicate cells', async () => {
    await controlPlane.createCell({ id: 'cell-1', capacity: 100 });

    await expect(
      controlPlane.createCell({ id: 'cell-1', capacity: 100 })
    ).rejects.toThrow('Cell already exists');
  });

  test('should get a cell', async () => {
    await controlPlane.createCell({ id: 'cell-1', capacity: 100 });
    const cell = await controlPlane.getCell('cell-1');

    expect(cell).toBeDefined();
    expect(cell?.id).toBe('cell-1');
  });

  test('should update cell status', async () => {
    await controlPlane.createCell({ id: 'cell-1', capacity: 100 });
    await controlPlane.updateCellStatus('cell-1', 'active');

    const cell = await controlPlane.getCell('cell-1');
    expect(cell?.status).toBe('active');
  });

  test('should assign tenant to cell', async () => {
    await controlPlane.createCell({ id: 'cell-1', capacity: 100 });
    await controlPlane.updateCellStatus('cell-1', 'active');
    await controlPlane.setTenantTier('tenant-1', 'regular');
    await controlPlane.assignTenantToCell('tenant-1', 'cell-1');

    const cell = await controlPlane.getCell('cell-1');
    expect(cell?.currentTenants).toBe(1);
  });

  test('should not assign tenant to inactive cell', async () => {
    await controlPlane.createCell({ id: 'cell-1', capacity: 100 });
    await controlPlane.setTenantTier('tenant-1', 'regular');

    await expect(
      controlPlane.assignTenantToCell('tenant-1', 'cell-1')
    ).rejects.toThrow('Cell is not active');
  });

  test('should not assign tenant to full cell', async () => {
    await controlPlane.createCell({ id: 'cell-1', capacity: 1 });
    await controlPlane.updateCellStatus('cell-1', 'active');
    await controlPlane.setTenantTier('tenant-1', 'regular');
    await controlPlane.assignTenantToCell('tenant-1', 'cell-1');

    await controlPlane.setTenantTier('tenant-2', 'regular');
    await expect(
      controlPlane.assignTenantToCell('tenant-2', 'cell-1')
    ).rejects.toThrow('Cell is at capacity');
  });

  test('should get all cells', async () => {
    await controlPlane.createCell({ id: 'cell-1', capacity: 100 });
    await controlPlane.createCell({ id: 'cell-2', capacity: 100 });

    const cells = await controlPlane.getAllCells();
    expect(cells.length).toBe(2);
  });
});


