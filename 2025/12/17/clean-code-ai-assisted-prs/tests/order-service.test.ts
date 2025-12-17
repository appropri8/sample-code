// Tests for clean OrderService
// Demonstrates how clean code is easy to test

import { OrderService, OrderProcessingError, UserRepository, TaxCalculator, UserWithOrders } from '../src/after/order-service';
import { Order } from '../src/types';

describe('OrderService', () => {
  let orderService: OrderService;
  let mockUserRepository: jest.Mocked<UserRepository>;
  let mockTaxCalculator: jest.Mocked<TaxCalculator>;
  
  beforeEach(() => {
    mockUserRepository = {
      findById: jest.fn()
    };
    
    mockTaxCalculator = {
      calculate: jest.fn((amount) => amount * 0.1)
    };
    
    orderService = new OrderService(mockUserRepository, mockTaxCalculator);
  });
  
  describe('processUserOrders', () => {
    it('processes active orders for a user', async () => {
      const mockUser = {
        id: 'user123',
        orders: [
          { 
            id: 'order1', 
            userId: 'user123',
            status: 'pending' as const, 
            items: [{ productId: 'prod1', quantity: 2, price: 10 }] 
          },
          { 
            id: 'order2', 
            userId: 'user123',
            status: 'completed' as const, 
            items: [{ productId: 'prod2', quantity: 1, price: 20 }] 
          },
          { 
            id: 'order3', 
            userId: 'user123',
            status: 'processing' as const, 
            items: [{ productId: 'prod3', quantity: 3, price: 5 }] 
          }
        ]
      };
      
      mockUserRepository.findById.mockResolvedValue(mockUser);
      
      const result = await orderService.processUserOrders({ user: { id: 'user123' } });
      
      expect(result.orders).toHaveLength(2); // Only pending and processing
      expect(result.userId).toBe('user123');
      expect(result.count).toBe(2);
      expect(result.orders[0].id).toBe('order1');
      expect(result.orders[0].total).toBe(22); // 20 + 2 tax (10%)
      expect(result.orders[1].id).toBe('order3');
      expect(result.orders[1].total).toBe(16.5); // 15 + 1.5 tax
    });
    
    it('filters out completed and cancelled orders', async () => {
      const mockUser = {
        id: 'user123',
        orders: [
          { 
            id: 'order1', 
            userId: 'user123',
            status: 'completed' as const, 
            items: [{ productId: 'prod1', quantity: 1, price: 10 }] 
          },
          { 
            id: 'order2', 
            userId: 'user123',
            status: 'cancelled' as const, 
            items: [{ productId: 'prod2', quantity: 1, price: 20 }] 
          }
        ]
      };
      
      mockUserRepository.findById.mockResolvedValue(mockUser);
      
      const result = await orderService.processUserOrders({ user: { id: 'user123' } });
      
      expect(result.orders).toHaveLength(0);
      expect(result.count).toBe(0);
    });
    
    it('throws error when user ID is missing', async () => {
      await expect(
        orderService.processUserOrders({ user: { id: '' } })
      ).rejects.toThrow(OrderProcessingError);
      
      await expect(
        orderService.processUserOrders({ user: { id: '' } })
      ).rejects.toThrow('Invalid user data: user ID is required');
    });
    
    it('calculates tax correctly for each order', async () => {
      const mockUser = {
        id: 'user123',
        orders: [
          { 
            id: 'order1', 
            userId: 'user123',
            status: 'pending' as const, 
            items: [{ productId: 'prod1', quantity: 1, price: 100 }] 
          }
        ]
      };
      
      mockUserRepository.findById.mockResolvedValue(mockUser);
      mockTaxCalculator.calculate.mockReturnValue(10); // 10% tax
      
      const result = await orderService.processUserOrders({ user: { id: 'user123' } });
      
      expect(mockTaxCalculator.calculate).toHaveBeenCalledWith(100);
      expect(result.orders[0].total).toBe(110); // 100 + 10 tax
    });
    
    it('handles empty orders list', async () => {
      const mockUser = {
        id: 'user123',
        orders: []
      };
      
      mockUserRepository.findById.mockResolvedValue(mockUser);
      
      const result = await orderService.processUserOrders({ user: { id: 'user123' } });
      
      expect(result.orders).toHaveLength(0);
      expect(result.count).toBe(0);
    });
  });
});
