// AFTER: Clean service with early returns and clear methods
// Improvements: specific methods, early returns, clear error handling

import { User, Order } from '../types';

export class UserServiceError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'UserServiceError';
  }
}

export interface OrderRepository {
  findByUserId(userId: string): Promise<Order[]>;
}

export interface UserRepository {
  findById(userId: string): Promise<User | null>;
}

export class UserService {
  constructor(
    private orderRepository: OrderRepository,
    private userRepository: UserRepository
  ) {}
  
  async getUserOrders(userId: string): Promise<Order[]> {
    this.validateUserId(userId);
    
    const orders = await this.orderRepository.findByUserId(userId);
    
    if (orders.length === 0) {
      throw new UserServiceError(`No orders found for user ${userId}`);
    }
    
    return orders;
  }
  
  async getUserProfile(userId: string): Promise<User> {
    this.validateUserId(userId);
    
    const user = await this.userRepository.findById(userId);
    
    if (!user) {
      throw new UserServiceError(`User ${userId} not found`);
    }
    
    return user;
  }
  
  private validateUserId(userId: string): void {
    if (!userId || userId.length === 0) {
      throw new UserServiceError('User ID is required');
    }
  }
}
