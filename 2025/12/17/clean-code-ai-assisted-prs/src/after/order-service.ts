// AFTER: Clean, refactored code
// Improvements: clear names, linear flow, explicit dependencies, consistent errors

import { Order, ProcessOrderRequest, ProcessOrderResult, ProcessedOrder, OrderItem } from '../types';

export class OrderProcessingError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'OrderProcessingError';
  }
}

export interface UserRepository {
  findById(userId: string): Promise<UserWithOrders>;
}

export interface UserWithOrders {
  id: string;
  orders: Order[];
}

export interface TaxCalculator {
  calculate(subtotal: number): number;
}

export class OrderService {
  constructor(
    private userRepository: UserRepository,
    private taxCalculator: TaxCalculator
  ) {}
  
  async processUserOrders(request: ProcessOrderRequest): Promise<ProcessOrderResult> {
    this.validateRequest(request);
    
    const user = await this.userRepository.findById(request.user.id);
    const activeOrders = this.filterActiveOrders(user.orders);
    const processedOrders = await this.processOrders(activeOrders, user.id);
    
    return {
      orders: processedOrders,
      userId: user.id,
      count: processedOrders.length
    };
  }
  
  private validateRequest(request: ProcessOrderRequest): void {
    if (!request?.user?.id) {
      throw new OrderProcessingError('Invalid user data: user ID is required');
    }
  }
  
  private filterActiveOrders(orders: Order[]): Order[] {
    return orders.filter(order => 
      order?.status === 'pending' || order?.status === 'processing'
    );
  }
  
  private async processOrders(orders: Order[], userId: string): Promise<ProcessedOrder[]> {
    const processedOrders: ProcessedOrder[] = [];
    
    for (const order of orders) {
      const orderTotal = this.calculateOrderTotal(order);
      const tax = this.taxCalculator.calculate(orderTotal);
      const finalTotal = orderTotal + tax;
      
      if (finalTotal > 0) {
        processedOrders.push({
          id: order.id,
          userId,
          total: finalTotal,
          status: order.status as 'pending' | 'processing',
          items: order.items || []
        });
      }
    }
    
    return processedOrders;
  }
  
  private calculateOrderTotal(order: Order): number {
    if (!order.items || order.items.length === 0) {
      return 0;
    }
    
    return order.items.reduce(
      (total, item) => total + (item.price * item.quantity),
      0
    );
  }
}
