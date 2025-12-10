import { Pool, QueryResult } from 'pg';

export interface IdempotencyRecord {
  idempotency_key: string;
  status: 'processing' | 'completed' | 'failed';
  response_hash?: string;
  response_body?: string;
  user_id?: string;
  endpoint?: string;
  request_hash?: string;
  created_at: Date;
  expires_at: Date;
}

export class IdempotencyStore {
  private pool: Pool;

  constructor(pool: Pool) {
    this.pool = pool;
  }

  async findByIdempotencyKey(key: string): Promise<IdempotencyRecord | null> {
    const result = await this.pool.query(
      `SELECT * FROM idempotency_keys 
       WHERE idempotency_key = $1 AND expires_at > NOW()`,
      [key]
    );

    if (result.rows.length === 0) {
      return null;
    }

    return this.mapRowToRecord(result.rows[0]);
  }

  async createProcessingRecord(
    key: string,
    userId: string | undefined,
    endpoint: string,
    requestHash: string,
    ttlHours: number = 24
  ): Promise<IdempotencyRecord> {
    const expiresAt = new Date();
    expiresAt.setHours(expiresAt.getHours() + ttlHours);

    try {
      const result = await this.pool.query(
        `INSERT INTO idempotency_keys 
         (idempotency_key, status, user_id, endpoint, request_hash, created_at, expires_at)
         VALUES ($1, $2, $3, $4, $5, NOW(), $6)
         RETURNING *`,
        [key, 'processing', userId, endpoint, requestHash, expiresAt]
      );

      return this.mapRowToRecord(result.rows[0]);
    } catch (error: any) {
      if (error.code === '23505') {
        // Unique constraint violation - key already exists
        throw new Error('Idempotency key already exists');
      }
      throw error;
    }
  }

  async updateCompleted(
    key: string,
    responseBody: string,
    responseHash: string
  ): Promise<void> {
    await this.pool.query(
      `UPDATE idempotency_keys 
       SET status = 'completed', 
           response_body = $1, 
           response_hash = $2
       WHERE idempotency_key = $3`,
      [responseBody, responseHash, key]
    );
  }

  async updateFailed(key: string, errorMessage: string): Promise<void> {
    await this.pool.query(
      `UPDATE idempotency_keys 
       SET status = 'failed', 
           response_body = $1
       WHERE idempotency_key = $2`,
      [JSON.stringify({ error: errorMessage }), key]
    );
  }

  async cleanupExpired(): Promise<number> {
    const result = await this.pool.query(
      `DELETE FROM idempotency_keys WHERE expires_at < NOW()`
    );
    return result.rowCount || 0;
  }

  private mapRowToRecord(row: any): IdempotencyRecord {
    return {
      idempotency_key: row.idempotency_key,
      status: row.status,
      response_hash: row.response_hash,
      response_body: row.response_body,
      user_id: row.user_id,
      endpoint: row.endpoint,
      request_hash: row.request_hash,
      created_at: new Date(row.created_at),
      expires_at: new Date(row.expires_at),
    };
  }
}

// Database schema SQL
export const IDEMPOTENCY_SCHEMA = `
CREATE TABLE IF NOT EXISTS idempotency_keys (
  idempotency_key VARCHAR(255) PRIMARY KEY,
  status VARCHAR(50) NOT NULL CHECK (status IN ('processing', 'completed', 'failed')),
  response_hash VARCHAR(64),
  response_body TEXT,
  user_id VARCHAR(255),
  endpoint VARCHAR(255),
  request_hash VARCHAR(64),
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  expires_at TIMESTAMP NOT NULL,
  INDEX idx_user_endpoint (user_id, endpoint),
  INDEX idx_expires_at (expires_at)
);

CREATE TABLE IF NOT EXISTS orders (
  id SERIAL PRIMARY KEY,
  order_id VARCHAR(255) UNIQUE NOT NULL,
  idempotency_key VARCHAR(255) UNIQUE NOT NULL,
  user_id VARCHAR(255) NOT NULL,
  cart_id VARCHAR(255) NOT NULL,
  status VARCHAR(50) NOT NULL DEFAULT 'pending',
  total_amount DECIMAL(10, 2) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  INDEX idx_user_id (user_id),
  INDEX idx_idempotency_key (idempotency_key)
);

CREATE TABLE IF NOT EXISTS processed_messages (
  id SERIAL PRIMARY KEY,
  idempotency_key VARCHAR(255) UNIQUE NOT NULL,
  topic VARCHAR(255) NOT NULL,
  partition INTEGER,
  offset BIGINT,
  processed_at TIMESTAMP NOT NULL DEFAULT NOW(),
  INDEX idx_idempotency_key (idempotency_key)
);
`;
