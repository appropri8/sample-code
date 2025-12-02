/**
 * Tenant-aware repository pattern.
 * 
 * This module demonstrates how to enforce tenant isolation
 * at the repository layer, making it impossible to forget
 * tenant filters.
 */

import { Pool, PoolClient } from 'pg';
import { Order } from './types';

/**
 * Base repository class that enforces tenant isolation.
 * All queries automatically include tenant_id filter.
 */
export abstract class TenantAwareRepository<T> {
  constructor(
    protected db: Pool,
    protected tenantId: string
  ) {
    if (!tenantId) {
      throw new Error('Tenant ID required for repository');
    }
  }
  
  /**
   * Add tenant filter to WHERE clause.
   */
  protected addTenantFilter(query: string, params: any[]): [string, any[]] {
    const hasWhere = query.toUpperCase().includes('WHERE');
    const separator = hasWhere ? 'AND' : 'WHERE';
    return [
      `${query} ${separator} tenant_id = $${params.length + 1}`,
      [...params, this.tenantId]
    ];
  }
  
  /**
   * Execute query with automatic tenant filtering.
   */
  protected async queryWithTenant(
    query: string,
    params: any[] = []
  ): Promise<any> {
    const [filteredQuery, filteredParams] = this.addTenantFilter(query, params);
    return this.db.query(filteredQuery, filteredParams);
  }
}

/**
 * Order repository with tenant isolation enforced.
 */
export class OrderRepository extends TenantAwareRepository<Order> {
  /**
   * Find all orders for this tenant.
   * Tenant filter is automatically applied.
   */
  async findAll(): Promise<Order[]> {
    const result = await this.queryWithTenant('SELECT * FROM orders');
    return result.rows;
  }
  
  /**
   * Find order by ID for this tenant.
   * Even if ID matches another tenant's order, it won't be returned.
   */
  async findById(id: string): Promise<Order | null> {
    const result = await this.queryWithTenant(
      'SELECT * FROM orders WHERE id = $1',
      [id]
    );
    return result.rows[0] || null;
  }
  
  /**
   * Find orders by user ID for this tenant.
   */
  async findByUserId(userId: string): Promise<Order[]> {
    const result = await this.queryWithTenant(
      'SELECT * FROM orders WHERE user_id = $1',
      [userId]
    );
    return result.rows;
  }
  
  /**
   * Create order for this tenant.
   * Tenant ID is automatically set.
   */
  async create(order: Omit<Order, 'id' | 'tenantId' | 'createdAt'>): Promise<Order> {
    const result = await this.queryWithTenant(
      `INSERT INTO orders (tenant_id, user_id, amount, status, created_at)
       VALUES ($1, $2, $3, $4, NOW())
       RETURNING *`,
      [this.tenantId, order.userId, order.amount, order.status]
    );
    return result.rows[0];
  }
  
  /**
   * Update order for this tenant.
   * Only updates if order belongs to this tenant.
   */
  async update(id: string, updates: Partial<Order>): Promise<Order | null> {
    const setClause: string[] = [];
    const values: any[] = [];
    let paramIndex = 1;
    
    if (updates.amount !== undefined) {
      setClause.push(`amount = $${paramIndex++}`);
      values.push(updates.amount);
    }
    if (updates.status !== undefined) {
      setClause.push(`status = $${paramIndex++}`);
      values.push(updates.status);
    }
    
    if (setClause.length === 0) {
      return this.findById(id);
    }
    
    values.push(id);
    const result = await this.queryWithTenant(
      `UPDATE orders 
       SET ${setClause.join(', ')}
       WHERE id = $${paramIndex}
       RETURNING *`,
      values
    );
    
    return result.rows[0] || null;
  }
  
  /**
   * Delete order for this tenant.
   * Only deletes if order belongs to this tenant.
   */
  async delete(id: string): Promise<boolean> {
    const result = await this.queryWithTenant(
      'DELETE FROM orders WHERE id = $1 RETURNING id',
      [id]
    );
    return result.rows.length > 0;
  }
}

/**
 * Alternative: Repository factory that requires tenant ID.
 */
export class RepositoryFactory {
  constructor(private db: Pool) {}
  
  createOrderRepository(tenantId: string): OrderRepository {
    if (!tenantId) {
      throw new Error('Tenant ID required to create repository');
    }
    return new OrderRepository(this.db, tenantId);
  }
}

/**
 * Example: Using repository with tenant context.
 */
export function createOrderRepositoryForTenant(
  db: Pool,
  tenantId: string
): OrderRepository {
  // This will throw if tenantId is missing
  return new OrderRepository(db, tenantId);
}

