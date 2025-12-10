import { Pool } from 'pg';
import { Order, CreateOrderRequest } from './types';
import { v4 as uuidv4 } from 'uuid';

export class OrderService {
  private pool: Pool;

  constructor(pool: Pool) {
    this.pool = pool;
  }

  async createOrder(
    request: CreateOrderRequest,
    idempotencyKey: string
  ): Promise<Order> {
    return await this.pool.query('BEGIN').then(async () => {
      try {
        // Check if order already exists with this idempotency key
        const existingResult = await this.pool.query(
          `SELECT * FROM orders WHERE idempotency_key = $1`,
          [idempotencyKey]
        );

        if (existingResult.rows.length > 0) {
          // Order already exists - return it
          return this.mapRowToOrder(existingResult.rows[0]);
        }

        // Calculate total
        const totalAmount = request.items.reduce(
          (sum, item) => sum + item.price * item.quantity,
          0
        );

        // Create new order
        const orderId = uuidv4();
        const result = await this.pool.query(
          `INSERT INTO orders 
           (order_id, idempotency_key, user_id, cart_id, status, total_amount)
           VALUES ($1, $2, $3, $4, $5, $6)
           RETURNING *`,
          [
            orderId,
            idempotencyKey,
            request.user_id,
            request.cart_id,
            'pending',
            totalAmount,
          ]
        );

        await this.pool.query('COMMIT');

        const order = this.mapRowToOrder(result.rows[0]);
        order.items = request.items;
        return order;
      } catch (error) {
        await this.pool.query('ROLLBACK');
        throw error;
      }
    });
  }

  async getOrder(orderId: string): Promise<Order | null> {
    const result = await this.pool.query(
      `SELECT * FROM orders WHERE order_id = $1`,
      [orderId]
    );

    if (result.rows.length === 0) {
      return null;
    }

    return this.mapRowToOrder(result.rows[0]);
  }

  private mapRowToOrder(row: any): Order {
    return {
      order_id: row.order_id,
      user_id: row.user_id,
      cart_id: row.cart_id,
      status: row.status,
      total_amount: parseFloat(row.total_amount),
      items: [], // Loaded separately if needed
      created_at: new Date(row.created_at),
    };
  }
}
