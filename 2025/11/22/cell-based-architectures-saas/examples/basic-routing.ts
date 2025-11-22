import { CellDirectory } from '../src/cell-directory';
import { CellRouter } from '../src/cell-router';
import { ControlPlaneAPI } from '../src/control-plane';

async function main() {
  console.log('=== Basic Cell Routing Example ===\n');

  // Create control plane
  const controlPlane = new ControlPlaneAPI();

  // Create some cells
  await controlPlane.createCell({ id: 'cell-1', capacity: 100 });
  await controlPlane.createCell({ id: 'cell-2', capacity: 100 });
  await controlPlane.createCell({ id: 'cell-3', capacity: 100 });

  // Activate cells
  await controlPlane.updateCellStatus('cell-1', 'active');
  await controlPlane.updateCellStatus('cell-2', 'active');
  await controlPlane.updateCellStatus('cell-3', 'active');

  // Create cell directory
  const directory = new CellDirectory(controlPlane);

  // Create router
  const cellBaseUrls = new Map([
    ['cell-1', 'http://cell-1.internal'],
    ['cell-2', 'http://cell-2.internal'],
    ['cell-3', 'http://cell-3.internal']
  ]);
  const router = new CellRouter(directory, cellBaseUrls);

  // Create some tenants
  await controlPlane.setTenantTier('tenant-1', 'regular');
  await controlPlane.setTenantTier('tenant-2', 'enterprise');
  await controlPlane.setTenantTier('tenant-3', 'vip');

  // Assign tenants to cells
  await controlPlane.assignTenantToCell('tenant-1', 'cell-1');
  await controlPlane.assignTenantToCell('tenant-2', 'cell-2');
  await controlPlane.assignTenantToCell('tenant-3', 'cell-3');

  // Route requests
  console.log('Routing requests...\n');

  // Request 1: JWT token
  const request1 = {
    headers: {
      'authorization': 'Bearer ' + Buffer.from(JSON.stringify({ tenantId: 'tenant-1' })).toString('base64'),
      'host': 'api.example.com'
    },
    method: 'GET',
    url: 'https://api.example.com/orders'
  };

  const response1 = await router.route(request1);
  console.log('Request 1 (JWT):', response1.status, response1.body);

  // Request 2: Header
  const request2 = {
    headers: {
      'x-tenant-id': 'tenant-2',
      'host': 'api.example.com'
    },
    method: 'GET',
    url: 'https://api.example.com/orders'
  };

  const response2 = await router.route(request2);
  console.log('Request 2 (Header):', response2.status, response2.body);

  // Request 3: Subdomain
  const request3 = {
    headers: {
      'host': 'tenant-3.example.com'
    },
    method: 'GET',
    url: 'https://tenant-3.example.com/orders'
  };

  const response3 = await router.route(request3);
  console.log('Request 3 (Subdomain):', response3.status, response3.body);

  // Request 4: Missing tenant ID
  const request4 = {
    headers: {
      'host': 'api.example.com'
    },
    method: 'GET',
    url: 'https://api.example.com/orders'
  };

  const response4 = await router.route(request4);
  console.log('Request 4 (No Tenant ID):', response4.status, response4.body);

  console.log('\n=== Example Complete ===');
}

main().catch(console.error);


