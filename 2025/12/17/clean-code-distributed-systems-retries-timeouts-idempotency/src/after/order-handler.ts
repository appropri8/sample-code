/**
 * AFTER: Clean message handler
 * 
 * Improvements:
 * - Validation separated
 * - Idempotency explicit
 * - Business logic pure
 * - Each step is clear and testable
 */

import { ensureIdempotent, IdempotencyStore } from '../resilience';
import { OrderMessage, Order, OrderItem } from '../types';

// Validation separated from business logic
export class ValidationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'ValidationError';
  }
}

function validateOrderMessage(message: OrderMessage): void {
  if (!message.messageId) {
    throw new ValidationError('messageId is required');
  }
  if (!message.orderId) {
    throw new ValidationError('orderId is required');
  }
  if (!message.userId) {
    throw new ValidationError('userId is required');
  }
  if (!message.items || message.items.length === 0) {
    throw new ValidationError('items are required');
  }
}

// Business logic - pure function
async function processOrder(
  message: OrderMessage,
  orderRepository: OrderRepository,
  paymentService: PaymentService,
  inventoryService: InventoryService
): Promise<Order> {
  const order: Order = {
    id: message.orderId,
    userId: message.userId,
    items: message.items,
    total: message.items.reduce((sum, item) => sum + (item.price * item.quantity), 0),
    status: 'pending'
  };

  await orderRepository.create(order);
  await paymentService.charge(order.total, message.userId);
  await inventoryService.reserveItems(message.items);

  return order;
}

// Interfaces for dependencies
interface OrderRepository {
  create(order: Order): Promise<void>;
}

interface PaymentService {
  charge(amount: number, userId: string): Promise<void>;
}

interface InventoryService {
  reserveItems(items: OrderItem[]): Promise<void>;
}

interface MessageQueue {
  ack(messageId: string): Promise<void>;
}

export class OrderHandler {
  constructor(
    private orderRepository: OrderRepository,
    private paymentService: PaymentService,
    private inventoryService: InventoryService,
    private messageQueue: MessageQueue,
    private idempotencyStore: IdempotencyStore
  ) {}

  /**
   * Handle order message - clean and readable
   * You can see from the function that it:
   * - Validates the message
   * - Ensures idempotency
   * - Processes the order
   * - Acks the message
   */
  async handleOrderMessage(message: OrderMessage): Promise<Order> {
    // Step 1: Validate
    validateOrderMessage(message);

    // Step 2: Ensure idempotency (explicit)
    const order = await ensureIdempotent(
      () => processOrder(
        message,
        this.orderRepository,
        this.paymentService,
        this.inventoryService
      ),
      {
        idempotencyKey: message.messageId,
        idempotencyStore: this.idempotencyStore,
        ttlSeconds: 3600
      }
    );

    // Step 3: Ack message
    await this.messageQueue.ack(message.messageId);

    return order;
  }
}
