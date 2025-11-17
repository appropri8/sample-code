const Database = require('./database');

class BackfillWorker {
  constructor(db, config = {}) {
    this.db = db;
    this.batchSize = config.batchSize || 1000;
    this.throttleMs = config.throttleMs || 100;
    this.resumeTokenKey = config.resumeTokenKey || 'backfill_orders_status';
    this.metrics = {
      rowsProcessed: 0,
      rowsPerSecond: 0,
      lag: 0,
      startTime: Date.now(),
      errors: 0
    };
  }

  async getResumeToken() {
    const result = await this.db.query(
      'SELECT last_processed_id FROM backfill_progress WHERE job_name = $1',
      [this.resumeTokenKey]
    );
    return result.rows[0]?.last_processed_id || 0;
  }

  async saveResumeToken(lastId) {
    await this.db.query(
      `INSERT INTO backfill_progress (job_name, last_processed_id, updated_at)
       VALUES ($1, $2, NOW())
       ON CONFLICT (job_name) 
       DO UPDATE SET last_processed_id = $2, updated_at = NOW()`,
      [this.resumeTokenKey, lastId]
    );
  }

  async processBatch() {
    const lastId = await this.getResumeToken();
    
    try {
      const rows = await this.db.query(
        `SELECT id, old_status FROM orders
         WHERE id > $1 AND status IS NULL
         ORDER BY id
         LIMIT $2`,
        [lastId, this.batchSize]
      );
      
      if (rows.rows.length === 0) {
        return false; // Done
      }
      
      for (const row of rows.rows) {
        // Idempotent update: only update if status is still NULL
        await this.db.query(
          `UPDATE orders SET status = $1 WHERE id = $2 AND status IS NULL`,
          [row.old_status || 'pending', row.id]
        );
      }
      
      const newLastId = rows.rows[rows.rows.length - 1].id;
      await this.saveResumeToken(newLastId);
      
      // Update metrics
      this.metrics.rowsProcessed += rows.rows.length;
      const elapsed = (Date.now() - this.metrics.startTime) / 1000;
      this.metrics.rowsPerSecond = this.metrics.rowsProcessed / elapsed;
      this.metrics.lag = newLastId;
      
      // Log progress
      console.log(`Processed ${this.metrics.rowsProcessed} rows, ${this.metrics.rowsPerSecond.toFixed(2)} rows/sec, lag: ${this.metrics.lag}`);
      
      return true; // More to process
    } catch (error) {
      this.metrics.errors++;
      console.error('Batch processing error', { error: error.message, lastId });
      throw error;
    }
  }

  async shadowReadCompare(orderId) {
    try {
      const [oldResult, newResult] = await Promise.all([
        this.db.query('SELECT id, user_id, amount, old_status as status FROM orders WHERE id = $1', [orderId]),
        this.db.query('SELECT id, user_id, amount, status FROM orders WHERE id = $1', [orderId])
      ]);
      
      const old = oldResult.rows[0];
      const new_ = newResult.rows[0];
      
      if (old && new_) {
        const oldNormalized = {
          id: old.id,
          user_id: old.user_id,
          amount: old.amount,
          status: old.status || 'pending'
        };
        const newNormalized = {
          id: new_.id,
          user_id: new_.user_id,
          amount: new_.amount,
          status: new_.status || 'pending'
        };
        
        if (JSON.stringify(oldNormalized) !== JSON.stringify(newNormalized)) {
          console.warn('Shadow read mismatch', { orderId, old: oldNormalized, new: newNormalized });
          return false;
        }
      }
      
      return true;
    } catch (error) {
      console.error('Shadow read error', { error: error.message, orderId });
      return false;
    }
  }

  async run() {
    console.log('Starting backfill...', {
      batchSize: this.batchSize,
      throttleMs: this.throttleMs,
      resumeTokenKey: this.resumeTokenKey
    });
    
    try {
      while (await this.processBatch()) {
        await this.sleep(this.throttleMs);
      }
      
      console.log('Backfill complete!', this.metrics);
      
      // Clear resume token when done
      await this.db.query('DELETE FROM backfill_progress WHERE job_name = $1', [this.resumeTokenKey]);
      
      return this.metrics;
    } catch (error) {
      console.error('Backfill failed', { error: error.message, metrics: this.metrics });
      throw error;
    }
  }

  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

module.exports = BackfillWorker;

