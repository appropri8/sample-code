import { ControlPlaneAPI } from '../src/control-plane';

async function main() {
  console.log('=== Control Plane Operations Example ===\n');

  const controlPlane = new ControlPlaneAPI();

  // Listen to events
  controlPlane.on('cell:provision', (data) => {
    console.log('Cell provisioning event:', data);
  });

  controlPlane.on('cell:status-change', (data) => {
    console.log('Cell status change:', data);
  });

  controlPlane.on('tenant:assigned', (data) => {
    console.log('Tenant assigned:', data);
  });

  // Create cells
  console.log('Creating cells...\n');

  const cell1 = await controlPlane.createCell({
    id: 'cell-shared-1',
    capacity: 1000,
    tier: 'shared'
  });
  console.log('Created cell:', cell1.id, 'Status:', cell1.status);

  const cell2 = await controlPlane.createCell({
    id: 'cell-enterprise-1',
    capacity: 100,
    tier: 'enterprise'
  });
  console.log('Created cell:', cell2.id, 'Status:', cell2.status);

  const cell3 = await controlPlane.createCell({
    id: 'cell-vip-1',
    capacity: 10,
    tier: 'vip'
  });
  console.log('Created cell:', cell3.id, 'Status:', cell3.status);

  // Activate cells
  console.log('\nActivating cells...\n');
  await controlPlane.updateCellStatus('cell-shared-1', 'active');
  await controlPlane.updateCellStatus('cell-enterprise-1', 'active');
  await controlPlane.updateCellStatus('cell-vip-1', 'active');

  // Get all cells
  console.log('\nAll cells:');
  const allCells = await controlPlane.getAllCells();
  allCells.forEach(cell => {
    console.log(`  ${cell.id}: ${cell.status}, ${cell.currentTenants}/${cell.capacity} tenants`);
  });

  // Assign tenants
  console.log('\nAssigning tenants...\n');

  // Regular tenants to shared cell
  for (let i = 1; i <= 5; i++) {
    await controlPlane.setTenantTier(`tenant-${i}`, 'regular');
    await controlPlane.assignTenantToCell(`tenant-${i}`, 'cell-shared-1');
    console.log(`Assigned tenant-${i} to cell-shared-1`);
  }

  // Enterprise tenant
  await controlPlane.setTenantTier('tenant-enterprise-1', 'enterprise');
  await controlPlane.assignTenantToCell('tenant-enterprise-1', 'cell-enterprise-1');
  console.log('Assigned tenant-enterprise-1 to cell-enterprise-1');

  // VIP tenant
  await controlPlane.setTenantTier('tenant-vip-1', 'vip');
  await controlPlane.assignTenantToCell('tenant-vip-1', 'cell-vip-1');
  console.log('Assigned tenant-vip-1 to cell-vip-1');

  // Check cell status
  console.log('\nCell status after assignments:');
  const updatedCells = await controlPlane.getAllCells();
  updatedCells.forEach(cell => {
    console.log(`  ${cell.id}: ${cell.currentTenants}/${cell.capacity} tenants`);
  });

  // Get cell for tenant
  console.log('\nCell lookups:');
  const cellForTenant1 = await controlPlane.getCellForTenant('tenant-1');
  console.log(`  tenant-1 -> ${cellForTenant1}`);

  const cellForEnterprise = await controlPlane.getCellForTenant('tenant-enterprise-1');
  console.log(`  tenant-enterprise-1 -> ${cellForEnterprise}`);

  // Maintenance mode
  console.log('\nPutting cell in maintenance...');
  await controlPlane.updateCellStatus('cell-shared-1', 'maintenance');
  const maintenanceCell = await controlPlane.getCell('cell-shared-1');
  console.log(`  cell-shared-1 status: ${maintenanceCell?.status}`);

  console.log('\n=== Example Complete ===');
}

main().catch(console.error);


