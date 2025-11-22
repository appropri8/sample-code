import { ControlPlaneAPI } from '../src/control-plane';
import { CellDirectory } from '../src/cell-directory';
import { TenantRebalancer } from '../src/tenant-rebalancer';

async function main() {
  console.log('=== Tenant Rebalancing Example ===\n');

  const controlPlane = new ControlPlaneAPI();

  // Create cells
  console.log('Creating cells...\n');
  await controlPlane.createCell({ id: 'cell-1', capacity: 100 });
  await controlPlane.createCell({ id: 'cell-2', capacity: 100 });
  await controlPlane.updateCellStatus('cell-1', 'active');
  await controlPlane.updateCellStatus('cell-2', 'active');

  // Create directory
  const directory = new CellDirectory(controlPlane);

  // Create rebalancer
  const rebalancer = new TenantRebalancer(controlPlane, directory);

  // Assign initial tenants
  console.log('Assigning initial tenants...\n');
  for (let i = 1; i <= 10; i++) {
    await controlPlane.setTenantTier(`tenant-${i}`, 'regular');
    await controlPlane.assignTenantToCell(`tenant-${i}`, 'cell-1');
    console.log(`Assigned tenant-${i} to cell-1`);
  }

  // Check initial state
  console.log('\nInitial cell state:');
  const cell1 = await controlPlane.getCell('cell-1');
  const cell2 = await controlPlane.getCell('cell-2');
  console.log(`  cell-1: ${cell1?.currentTenants} tenants`);
  console.log(`  cell-2: ${cell2?.currentTenants} tenants`);

  // Rebalance: Move some tenants from cell-1 to cell-2
  console.log('\nRebalancing tenants...\n');

  const tenantsToMove = ['tenant-1', 'tenant-2', 'tenant-3'];
  for (const tenantId of tenantsToMove) {
    try {
      console.log(`Moving ${tenantId} from cell-1 to cell-2...`);
      await rebalancer.rebalanceTenant(tenantId, 'cell-2');
      console.log(`  ✓ Successfully moved ${tenantId}`);
    } catch (error) {
      console.error(`  ✗ Failed to move ${tenantId}:`, (error as Error).message);
    }
  }

  // Check final state
  console.log('\nFinal cell state:');
  const finalCell1 = await controlPlane.getCell('cell-1');
  const finalCell2 = await controlPlane.getCell('cell-2');
  console.log(`  cell-1: ${finalCell1?.currentTenants} tenants`);
  console.log(`  cell-2: ${finalCell2?.currentTenants} tenants`);

  // Verify routing
  console.log('\nVerifying routing...\n');
  for (const tenantId of tenantsToMove) {
    const cell = await controlPlane.getCellForTenant(tenantId);
    console.log(`  ${tenantId} -> ${cell}`);
  }

  // Show remaining tenants in cell-1
  console.log('\nRemaining tenants in cell-1:');
  for (let i = 4; i <= 10; i++) {
    const cell = await controlPlane.getCellForTenant(`tenant-${i}`);
    if (cell === 'cell-1') {
      console.log(`  tenant-${i}`);
    }
  }

  console.log('\n=== Example Complete ===');
}

main().catch(console.error);


