/**
 * Row-Level Security (RLS) implementation for PostgreSQL.
 * 
 * This module demonstrates how to use PostgreSQL RLS to enforce
 * tenant isolation at the database level, even if application
 * code has bugs.
 */

import { Pool, PoolClient } from 'pg';

/**
 * SQL for enabling RLS and creating tenant isolation policy.
 * Run this as database migration.
 */
export const RLS_MIGRATION_SQL = `
-- Enable Row Level Security on orders table
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;

-- Create policy: users can only access their tenant's orders
CREATE POLICY tenant_isolation_orders ON orders
  FOR ALL
  USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);

-- Enable RLS on users table
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Create policy: users can only access their tenant's users
CREATE POLICY tenant_isolation_users ON users
  FOR ALL
  USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);

-- Create function to set tenant context (for use in transactions)
CREATE OR REPLACE FUNCTION set_tenant_context(tenant_id_param uuid)
RETURNS void AS $$
BEGIN
  PERFORM set_config('app.current_tenant_id', tenant_id_param::text, true);
END;
$$ LANGUAGE plpgsql;
`;

/**
 * Set tenant context for the current database session.
 * This makes RLS automatically filter all queries to this tenant.
 */
export async function setTenantContext(
  client: PoolClient,
  tenantId: string
): Promise<void> {
  await client.query(
    "SELECT set_config('app.current_tenant_id', $1, true)",
    [tenantId]
  );
}

/**
 * Execute a function within tenant context.
 * All queries in the function will be automatically filtered by RLS.
 */
export async function withTenantContext<T>(
  pool: Pool,
  tenantId: string,
  fn: (client: PoolClient) => Promise<T>
): Promise<T> {
  const client = await pool.connect();
  try {
    await setTenantContext(client, tenantId);
    return await fn(client);
  } finally {
    client.release();
  }
}

/**
 * Example: Query orders with RLS automatically filtering.
 */
export async function getOrdersWithRLS(
  pool: Pool,
  tenantId: string
): Promise<any[]> {
  return withTenantContext(pool, tenantId, async (client) => {
    // Even without WHERE clause, RLS ensures only this tenant's orders are returned
    const result = await client.query('SELECT * FROM orders');
    return result.rows;
  });
}

/**
 * Example: Test that RLS prevents cross-tenant access.
 */
export async function testRLSIsolation(pool: Pool): Promise<void> {
  // Query as tenant-1
  const tenant1Orders = await getOrdersWithRLS(pool, 'tenant-1');
  console.log('Tenant-1 orders:', tenant1Orders.length);
  
  // Query as tenant-2
  const tenant2Orders = await getOrdersWithRLS(pool, 'tenant-2');
  console.log('Tenant-2 orders:', tenant2Orders.length);
  
  // Even if we try to query without tenant filter, RLS prevents cross-tenant access
  const allOrders = await pool.query('SELECT * FROM orders');
  // This will return empty if current_setting is not set, or only rows for the set tenant
  console.log('All orders (with RLS):', allOrders.rows.length);
}

/**
 * Create a database view that automatically filters by tenant.
 */
export const TENANT_VIEWS_SQL = `
-- Create view that requires tenant context
CREATE OR REPLACE VIEW tenant_orders AS
SELECT * FROM orders
WHERE tenant_id = current_setting('app.current_tenant_id', true)::uuid;

-- Application queries the view instead of the table
-- SELECT * FROM tenant_orders;
`;

