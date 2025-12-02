/**
 * Example: Row-Level Security (RLS) in PostgreSQL.
 * 
 * Demonstrates how RLS enforces tenant isolation at the database level,
 * even if application code has bugs.
 */

import { Pool } from 'pg';
import {
  setTenantContext,
  withTenantContext,
  getOrdersWithRLS,
  testRLSIsolation,
  RLS_MIGRATION_SQL
} from '../src/row-level-security';

const db = new Pool({
  host: process.env.DB_HOST || 'localhost',
  port: parseInt(process.env.DB_PORT || '5432'),
  database: process.env.DB_NAME || 'saas_db',
  user: process.env.DB_USER || 'postgres',
  password: process.env.DB_PASSWORD || 'postgres'
});

async function demonstrateRLS() {
  console.log('=== Row-Level Security Example ===\n');
  
  console.log('1. RLS Migration SQL:');
  console.log('   Run this to enable RLS on your tables:');
  console.log(RLS_MIGRATION_SQL);
  console.log('\n');
  
  console.log('2. Setting tenant context:');
  console.log('   When you set tenant context, all queries are automatically filtered\n');
  
  // Example: Query with tenant context
  try {
    const client = await db.connect();
    
    // Set tenant context for tenant-1
    await setTenantContext(client, 'tenant-1');
    console.log('   Set tenant context to: tenant-1');
    
    // Query orders - RLS automatically filters to tenant-1's orders
    const result = await client.query('SELECT * FROM orders');
    console.log(`   Found ${result.rows.length} orders for tenant-1`);
    console.log('   Even without WHERE clause, RLS ensures only tenant-1\'s data\n');
    
    // Set tenant context for tenant-2
    await setTenantContext(client, 'tenant-2');
    console.log('   Set tenant context to: tenant-2');
    
    const result2 = await client.query('SELECT * FROM orders');
    console.log(`   Found ${result2.rows.length} orders for tenant-2`);
    console.log('   RLS automatically filters to tenant-2\'s data\n');
    
    client.release();
  } catch (error: any) {
    console.log('   Error (expected if database/RLS not set up):', error.message);
    console.log('   To test RLS:');
    console.log('   1. Create database and tables');
    console.log('   2. Run RLS_MIGRATION_SQL');
    console.log('   3. Insert test data for multiple tenants');
    console.log('   4. Run this example\n');
  }
  
  console.log('3. Using withTenantContext helper:');
  console.log('   This helper automatically sets tenant context and cleans up\n');
  
  try {
    await withTenantContext(db, 'tenant-1', async (client) => {
      const result = await client.query('SELECT * FROM orders');
      console.log(`   Queried ${result.rows.length} orders for tenant-1`);
      console.log('   Tenant context automatically set and cleaned up\n');
    });
  } catch (error: any) {
    console.log('   Error (expected if database not set up):', error.message);
  }
  
  console.log('4. Testing RLS isolation:');
  console.log('   This demonstrates that RLS prevents cross-tenant access\n');
  
  try {
    await testRLSIsolation(db);
  } catch (error: any) {
    console.log('   Error (expected if database not set up):', error.message);
  }
  
  console.log('=== Key Points ===');
  console.log('- RLS enforces isolation at database level');
  console.log('- Even buggy code can\'t access wrong tenant\'s data');
  console.log('- Set tenant context before queries');
  console.log('- RLS policies automatically filter all queries');
  console.log('- Use withTenantContext for automatic cleanup');
  
  await db.end();
}

// Run example
demonstrateRLS().catch(console.error);

