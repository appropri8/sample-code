/**
 * Example: Tenant-safe data access.
 * 
 * Demonstrates how repositories enforce tenant isolation
 * and prevent queries without tenant filters.
 */

import { Pool } from 'pg';
import { OrderRepository, RepositoryFactory } from '../src/tenant-repository';

// Mock database connection (in real implementation, use actual connection)
const db = new Pool({
  host: 'localhost',
  port: 5432,
  database: 'saas_db',
  user: 'postgres',
  password: 'postgres'
});

async function demonstrateTenantIsolation() {
  console.log('=== Tenant-Aware Repository Example ===\n');
  
  // Create repository factory
  const factory = new RepositoryFactory(db);
  
  // Create repository for tenant-1
  // This will throw if tenantId is missing
  const tenant1Repo = factory.createOrderRepository('tenant-1');
  
  console.log('1. Created repository for tenant-1');
  console.log('   All queries will automatically filter by tenant_id = "tenant-1"\n');
  
  // Find all orders for tenant-1
  // This query automatically includes: WHERE tenant_id = 'tenant-1'
  try {
    const orders = await tenant1Repo.findAll();
    console.log(`2. Found ${orders.length} orders for tenant-1`);
    console.log('   Query executed: SELECT * FROM orders WHERE tenant_id = $1\n');
  } catch (error: any) {
    console.log('2. Error (expected if database not set up):', error.message);
  }
  
  // Create repository for tenant-2
  const tenant2Repo = factory.createOrderRepository('tenant-2');
  console.log('3. Created repository for tenant-2');
  console.log('   This repository can only access tenant-2\'s data\n');
  
  // Try to find order by ID
  // Even if the ID exists for another tenant, it won't be returned
  try {
    const order = await tenant2Repo.findById('order-123');
    if (order) {
      console.log('4. Found order:', order.id);
      console.log('   Even if order-123 exists for tenant-1, tenant-2 can\'t see it\n');
    } else {
      console.log('4. Order not found (or belongs to different tenant)\n');
    }
  } catch (error: any) {
    console.log('4. Error (expected if database not set up):', error.message);
  }
  
  // Demonstrate that repository requires tenant ID
  try {
    // @ts-ignore - This will throw at runtime
    const badRepo = new OrderRepository(db, '');
    console.log('5. This should not print');
  } catch (error: any) {
    console.log('5. Repository correctly rejects empty tenant ID');
    console.log(`   Error: ${error.message}\n`);
  }
  
  console.log('=== Key Points ===');
  console.log('- Repository requires tenant ID in constructor');
  console.log('- All queries automatically include tenant filter');
  console.log('- Impossible to query without tenant context');
  console.log('- Type system helps prevent mistakes');
}

// Run example
demonstrateTenantIsolation().catch(console.error);

