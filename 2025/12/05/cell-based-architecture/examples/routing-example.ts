import { InMemoryCellRouter } from '../src/router';

async function main() {
  const controlPlaneUrl = process.env.CONTROL_PLANE_URL || 'http://localhost:3001';
  const router = new InMemoryCellRouter(controlPlaneUrl);

  // Wait a bit for initial refresh
  await new Promise(resolve => setTimeout(resolve, 1000));

  // Test routing for different tenants
  const tenants = ['tenant-acme', 'tenant-beta', 'tenant-eu-corp', 'tenant-unknown'];

  console.log('Testing tenant-to-cell routing:\n');

  for (const tenantId of tenants) {
    const cellId = await router.getCellForTenant(tenantId);
    if (cellId) {
      console.log(`✓ Tenant ${tenantId} → Cell ${cellId}`);
    } else {
      console.log(`✗ Tenant ${tenantId} → No cell found`);
    }
  }

  console.log(`\nRouter cache size: ${router.getCacheSize()}`);

  router.stop();
}

main().catch(console.error);
