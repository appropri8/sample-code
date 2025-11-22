/**
 * Idempotent write endpoint implementation
 * 
 * Accepts Idempotency-Key header and stores/reuses results
 * to avoid double-charging or double-booking
 */

interface IdempotencyRecord {
  key: string;
  status: 'processing' | 'completed' | 'failed';
  result?: any;
  error?: string;
  requestHash: string;
  createdAt: Date;
  expiresAt: Date;
}

interface WriteRequest {
  idempotencyKey: string;
  operation: string;
  data: any;
}

class IdempotencyStore {
  private records: Map<string, IdempotencyRecord> = new Map();

  async get(key: string): Promise<IdempotencyRecord | null> {
    const record = this.records.get(key);
    if (!record) {
      return null;
    }
    
    // Check expiration
    if (record.expiresAt < new Date()) {
      this.records.delete(key);
      return null;
    }
    
    return record;
  }

  async set(record: IdempotencyRecord): Promise<void> {
    this.records.set(record.key, record);
  }

  async update(key: string, updates: Partial<IdempotencyRecord>): Promise<void> {
    const record = this.records.get(key);
    if (!record) {
      throw new Error(`Idempotency key not found: ${key}`);
    }
    
    Object.assign(record, updates);
    this.records.set(key, record);
  }
}

class IdempotentWriteService {
  constructor(
    private store: IdempotencyStore,
    private ttl: number = 24 * 60 * 60 * 1000 // 24 hours
  ) {}

  /**
   * Hash request body for validation
   */
  private hashRequest(data: any): string {
    const str = JSON.stringify(data);
    // Simple hash function (use crypto in production)
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash;
    }
    return Math.abs(hash).toString(16);
  }

  /**
   * Process write request with idempotency
   */
  async processWrite(
    request: WriteRequest,
    handler: (data: any) => Promise<any>
  ): Promise<any> {
    const { idempotencyKey, operation, data } = request;
    
    if (!idempotencyKey) {
      throw new Error('Idempotency-Key header required');
    }

    const requestHash = this.hashRequest(data);
    const now = new Date();
    const expiresAt = new Date(now.getTime() + this.ttl);

    // Check for existing record
    const existing = await this.store.get(idempotencyKey);
    
    if (existing) {
      // Validate request matches
      if (existing.requestHash !== requestHash) {
        throw new Error('Idempotency key reused with different request');
      }

      // Return cached result if completed
      if (existing.status === 'completed') {
        return existing.result;
      }

      // If processing, return conflict
      if (existing.status === 'processing') {
        throw new Error('Request already processing');
      }

      // If failed, allow retry (or throw based on your policy)
      // For this example, we allow retry
    }

    // Mark as processing
    await this.store.set({
      key: idempotencyKey,
      status: 'processing',
      requestHash,
      createdAt: now,
      expiresAt
    });

    try {
      // Process the request
      const result = await handler(data);

      // Store result
      await this.store.update(idempotencyKey, {
        status: 'completed',
        result
      });

      return result;
    } catch (error: any) {
      // Store error
      await this.store.update(idempotencyKey, {
        status: 'failed',
        error: error.message
      });

      throw error;
    }
  }
}

// Example usage
async function example() {
  const store = new IdempotencyStore();
  const service = new IdempotentWriteService(store);

  // Payment handler
  const processPayment = async (data: any) => {
    // Simulate payment processing
    await new Promise(resolve => setTimeout(resolve, 100));
    return {
      id: `payment-${Date.now()}`,
      amount: data.amount,
      status: 'completed',
      timestamp: new Date()
    };
  };

  const request: WriteRequest = {
    idempotencyKey: 'payment-123-abc',
    operation: 'create_payment',
    data: { amount: 100, currency: 'USD' }
  };

  // First call - processes
  const result1 = await service.processWrite(request, processPayment);
  console.log('First call:', result1);

  // Second call - returns cached result
  const result2 = await service.processWrite(request, processPayment);
  console.log('Second call (cached):', result2);
  console.log('Same result:', result1.id === result2.id);
}

export { IdempotentWriteService, IdempotencyStore, WriteRequest };

