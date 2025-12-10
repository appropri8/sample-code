import { createClient, RedisClientType } from 'redis';
import { hashString } from './utils';

export interface CachedResponse {
  status: 'completed' | 'failed';
  responseBody: string;
  responseHash: string;
  statusCode: number;
}

export class RedisIdempotencyStore {
  private client: RedisClientType;
  private defaultTtl: number;

  constructor(redisUrl?: string, defaultTtlSeconds: number = 86400) {
    this.client = createClient({
      url: redisUrl || 'redis://localhost:6379'
    });
    this.defaultTtl = defaultTtlSeconds;
  }

  async connect(): Promise<void> {
    await this.client.connect();
  }

  async disconnect(): Promise<void> {
    await this.client.disconnect();
  }

  async get(key: string): Promise<CachedResponse | null> {
    const cached = await this.client.get(`idempotency:${key}`);
    if (!cached) {
      return null;
    }
    return JSON.parse(cached);
  }

  async set(
    key: string,
    response: CachedResponse,
    ttlSeconds?: number
  ): Promise<void> {
    const ttl = ttlSeconds || this.defaultTtl;
    await this.client.setEx(
      `idempotency:${key}`,
      ttl,
      JSON.stringify(response)
    );
  }

  async setProcessing(
    key: string,
    requestHash: string,
    ttlSeconds?: number
  ): Promise<boolean> {
    // Use SET with NX (only if not exists) to prevent race conditions
    const ttl = ttlSeconds || this.defaultTtl;
    const result = await this.client.setNX(
      `idempotency:processing:${key}`,
      requestHash
    );

    if (result) {
      // Set expiration
      await this.client.expire(`idempotency:processing:${key}`, ttl);
    }

    return result;
  }

  async checkAndSet(
    key: string,
    requestHash: string
  ): Promise<'exists' | 'processing' | 'new'> {
    // Check if completed response exists
    const cached = await this.get(key);
    if (cached) {
      if (cached.responseHash !== requestHash) {
        throw new Error('Idempotency key reused with different request');
      }
      return 'exists';
    }

    // Check if processing
    const processing = await this.client.get(`idempotency:processing:${key}`);
    if (processing) {
      if (processing !== requestHash) {
        throw new Error('Idempotency key reused with different request');
      }
      return 'processing';
    }

    // Set as processing
    const set = await this.setProcessing(key, requestHash);
    if (!set) {
      // Race condition - another request set it first
      return 'processing';
    }

    return 'new';
  }

  async markCompleted(
    key: string,
    responseBody: string,
    statusCode: number = 200,
    ttlSeconds?: number
  ): Promise<void> {
    const responseHash = hashString(responseBody);
    const response: CachedResponse = {
      status: 'completed',
      responseBody,
      responseHash,
      statusCode,
    };

    await this.set(key, response, ttlSeconds);
    
    // Remove processing flag
    await this.client.del(`idempotency:processing:${key}`);
  }

  async markFailed(
    key: string,
    errorMessage: string,
    statusCode: number = 500,
    ttlSeconds?: number
  ): Promise<void> {
    const responseBody = JSON.stringify({ error: errorMessage });
    const responseHash = hashString(responseBody);
    const response: CachedResponse = {
      status: 'failed',
      responseBody,
      responseHash,
      statusCode,
    };

    await this.set(key, response, ttlSeconds);
    
    // Remove processing flag
    await this.client.del(`idempotency:processing:${key}`);
  }
}
