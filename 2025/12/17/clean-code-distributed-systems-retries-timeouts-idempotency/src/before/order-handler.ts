/**
 * BEFORE: Messy message handler
 * 
 * Problems:
 * - Idempotency logic mixed with business logic
 * - Validation scattered
 * - Hard to test
 * - Hard to see what the handler actually does
 */

export class OrderHandler {
  private processedMessages: Map<string, any> = new Map();

  async handleOrderMessage(message: any): Promise<any> {
    // Validation mixed with processing
    if (!message || !message.messageId) {
      throw new Error('Invalid message');
    }

    if (!message.orderId) {
      throw new Error('orderId is required');
    }

    if (!message.userId) {
      throw new Error('userId is required');
    }

    if (!message.items || message.items.length === 0) {
      throw new Error('items are required');
    }

    // Idempotency check mixed in
    if (this.processedMessages.has(message.messageId)) {
      console.log('Duplicate message, returning cached result');
      return this.processedMessages.get(message.messageId);
    }

    // Business logic mixed with everything else
    const order = {
      id: message.orderId,
      userId: message.userId,
      items: message.items,
      total: message.items.reduce((sum: number, item: any) => 
        sum + (item.price * item.quantity), 0),
      status: 'pending'
    };

    // More business logic
    await this.chargePayment(order.total, message.userId);
    await this.reserveInventory(message.items);

    // Store result for idempotency
    this.processedMessages.set(message.messageId, order);

    // Ack message (but what if this fails?)
    await this.ackMessage(message.messageId);

    return order;
  }

  private async chargePayment(amount: number, userId: string): Promise<void> {
    // Simulated payment
    await new Promise(resolve => setTimeout(resolve, 100));
  }

  private async reserveInventory(items: any[]): Promise<void> {
    // Simulated inventory reservation
    await new Promise(resolve => setTimeout(resolve, 100));
  }

  private async ackMessage(messageId: string): Promise<void> {
    // Simulated ack
    await new Promise(resolve => setTimeout(resolve, 50));
  }
}
