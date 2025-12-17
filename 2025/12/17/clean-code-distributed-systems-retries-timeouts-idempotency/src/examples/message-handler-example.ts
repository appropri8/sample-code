/**
 * Example: Message handler with idempotency
 * 
 * Demonstrates the clean pattern for async message handlers
 */

import { OrderHandler } from '../after/order-handler';
import { OrderMessage } from '../types';
import { IdempotencyStore } from '../resilience';

// Simple in-memory idempotency store for example
class MemoryIdempotencyStore implements IdempotencyStore {
  private store: Map<string, { value: any; expiresAt: number }> = new Map();

  async get<T>(key: string): Promise<T | null> {
    const entry = this.store.get(key);
    if (!entry) {
      return null;
    }
    if (Date.now() > entry.expiresAt) {
      this.store.delete(key);
      return null;
    }
    return entry.value as T;
  }

  async set<T>(key: string, value: T, ttlSeconds?: number): Promise<void> {
    const expiresAt = Date.now() + (ttlSeconds || 3600) * 1000;
    this.store.set(key, { value, expiresAt });
  }
}

// Mock implementations
const mockOrderRepository = {
  async create(order: any): Promise<void> {
    console.log('Creating order:', order.id);
  }
};

const mockPaymentService = {
  async charge(amount: number, userId: string): Promise<void> {
    console.log(`Charging ${amount} to user ${userId}`);
  }
};

const mockInventoryService = {
  async reserveItems(items: any[]): Promise<void> {
    console.log('Reserving items:', items.length);
  }
};

const mockMessageQueue = {
  async ack(messageId: string): Promise<void> {
    console.log('Acknowledging message:', messageId);
  }
};

async function main() {
  const idempotencyStore = new MemoryIdempotencyStore();
  const handler = new OrderHandler(
    mockOrderRepository,
    mockPaymentService,
    mockInventoryService,
    mockMessageQueue,
    idempotencyStore
  );

  const message: OrderMessage = {
    messageId: 'msg-123',
    orderId: 'order-456',
    userId: 'user-789',
    items: [
      { productId: 'prod-1', quantity: 2, price: 10.00 },
      { productId: 'prod-2', quantity: 1, price: 25.00 }
    ]
  };

  try {
    console.log('Processing order message...');
    const order = await handler.handleOrderMessage(message);
    console.log('Order processed:', order);

    // Try processing again (should return cached result)
    console.log('\nProcessing same message again (idempotency test)...');
    const order2 = await handler.handleOrderMessage(message);
    console.log('Order processed (from cache):', order2);
  } catch (error) {
    console.error('Failed to process message:', error);
  }
}

if (require.main === module) {
  main().catch(console.error);
}
