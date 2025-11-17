const Database = require('./database');

class OrderRepository {
  constructor(db) {
    this.db = db;
    this.readFromNew = process.env.READ_FROM_NEW === 'true';
    this.writeToNew = process.env.WRITE_TO_NEW === 'true';
    this.dualWrite = process.env.DUAL_WRITE === 'true';
  }

  async createOrder(orderData) {
    const client = await this.db.getClient();
    
    try {
      await client.query('BEGIN');
      
      // Determine status value
      const status = orderData.status || 'pending';
      
      if (this.dualWrite || this.writeToNew) {
        // Write to new schema
        const result = await client.query(
          `INSERT INTO orders (user_id, amount, status, created_at)
           VALUES ($1, $2, $3, $4)
           RETURNING id`,
          [orderData.userId, orderData.amount, status, new Date()]
        );
        
        const orderId = result.rows[0].id;
        
        // Also write to old schema for backward compatibility (if dual-write is enabled)
        if (this.dualWrite && orderData.oldStatus) {
          await client.query(
            `UPDATE orders SET old_status = $1 WHERE id = $2`,
            [orderData.oldStatus, orderId]
          );
        }
        
        await client.query('COMMIT');
        return { id: orderId, ...orderData, status };
      } else {
        // Write to old schema only (before migration)
        const result = await client.query(
          `INSERT INTO orders (user_id, amount, created_at)
           VALUES ($1, $2, $3)
           RETURNING id`,
          [orderData.userId, orderData.amount, new Date()]
        );
        
        await client.query('COMMIT');
        return { id: result.rows[0].id, ...orderData };
      }
    } catch (error) {
      await client.query('ROLLBACK');
      throw error;
    } finally {
      client.release();
    }
  }

  async getOrder(id) {
    if (this.readFromNew) {
      return await this.getOrderFromNew(id);
    } else {
      return await this.getOrderFromOld(id);
    }
  }

  async getOrderFromNew(id) {
    const result = await this.db.query(
      'SELECT * FROM orders WHERE id = $1',
      [id]
    );
    return result.rows[0] || null;
  }

  async getOrderFromOld(id) {
    const result = await this.db.query(
      'SELECT id, user_id, amount, created_at, old_status as status FROM orders WHERE id = $1',
      [id]
    );
    return result.rows[0] || null;
  }

  async shadowRead(id) {
    const [oldResult, newResult] = await Promise.all([
      this.getOrderFromOld(id),
      this.getOrderFromNew(id)
    ]);
    
    // Compare results
    if (oldResult && newResult) {
      const oldNormalized = {
        id: oldResult.id,
        user_id: oldResult.user_id,
        amount: oldResult.amount,
        status: oldResult.status || oldResult.old_status
      };
      const newNormalized = {
        id: newResult.id,
        user_id: newResult.user_id,
        amount: newResult.amount,
        status: newResult.status
      };
      
      if (JSON.stringify(oldNormalized) !== JSON.stringify(newNormalized)) {
        console.warn('Shadow read mismatch', { id, old: oldNormalized, new: newNormalized });
        return { mismatch: true, old: oldNormalized, new: newNormalized };
      }
    }
    
    return { mismatch: false, result: oldResult || newResult };
  }

  async createOrderWithRetry(orderData, maxRetries = 3) {
    for (let i = 0; i < maxRetries; i++) {
      try {
        return await this.createOrder(orderData);
      } catch (error) {
        if (i === maxRetries - 1) {
          throw error;
        }
        // Exponential backoff
        await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1)));
      }
    }
  }
}

module.exports = OrderRepository;

