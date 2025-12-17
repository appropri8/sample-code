// AFTER: Focused calculator class with clear responsibilities
// Improvements: domain-specific, single responsibility, clear naming

import { Order, OrderItem } from '../types';

export class OrderCalculator {
  calculateTotal(order: Order): number {
    if (!order.items || order.items.length === 0) {
      return 0;
    }
    
    return order.items.reduce(
      (total, item) => total + this.calculateItemTotal(item),
      0
    );
  }
  
  calculateItemTotal(item: OrderItem): number {
    return item.price * item.quantity;
  }
  
  calculateSubtotal(items: OrderItem[]): number {
    return items.reduce(
      (total, item) => total + this.calculateItemTotal(item),
      0
    );
  }
  
  applyDiscount(subtotal: number, discountPercent: number): number {
    if (discountPercent < 0 || discountPercent > 100) {
      throw new Error('Discount percent must be between 0 and 100');
    }
    
    return subtotal * (1 - discountPercent / 100);
  }
}
