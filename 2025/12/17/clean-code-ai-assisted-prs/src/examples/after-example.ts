// Complete AFTER example: Clean refactored code
// This demonstrates all the improvements from the article

import { OrderService, OrderProcessingError, UserWithOrders } from '../after/order-service';
import { UserService, UserServiceError } from '../after/user-service';
import { OrderCalculator } from '../after/order-calculator';
import { Order, User } from '../types';

// Mock implementations for demonstration
class MockUserRepository {
  private users: Map<string, UserWithOrders> = new Map();
  
  constructor() {
    this.users.set('user123', {
      id: 'user123',
      orders: [
        { 
          id: 'order1', 
          userId: 'user123',
          status: 'pending', 
          items: [{ productId: 'prod1', quantity: 2, price: 10 }] 
        },
        { 
          id: 'order2', 
          userId: 'user123',
          status: 'completed', 
          items: [{ productId: 'prod2', quantity: 1, price: 20 }] 
        },
        { 
          id: 'order3', 
          userId: 'user123',
          status: 'processing', 
          items: [{ productId: 'prod3', quantity: 3, price: 5 }] 
        }
      ]
    });
  }
  
  async findById(userId: string): Promise<UserWithOrders> {
    const user = this.users.get(userId);
    if (!user) {
      throw new Error(`User ${userId} not found`);
    }
    return user;
  }
}

class MockTaxCalculator {
  calculate(subtotal: number): number {
    return subtotal * 0.1; // 10% tax
  }
}

// Example usage of clean code
async function runAfterExample() {
  console.log('=== AFTER: Clean Refactored Code ===\n');
  
  // Example 1: Clean order service
  console.log('Example 1: OrderService.processUserOrders');
  const userRepo = new MockUserRepository();
  const taxCalc = new MockTaxCalculator();
  const orderService = new OrderService(userRepo, taxCalc);
  
  try {
    const result = await orderService.processUserOrders({
      user: { id: 'user123' }
    });
    
    console.log('Result:', JSON.stringify(result, null, 2));
    console.log('\nImprovements:');
    console.log('- Clear names (processUserOrders, filterActiveOrders)');
    console.log('- Linear flow with early returns');
    console.log('- Validation at boundaries');
    console.log('- Consistent error handling');
    console.log('- Explicit dependencies (injected)\n');
  } catch (error) {
    if (error instanceof OrderProcessingError) {
      console.log('Error:', error.message);
    } else {
      console.log('Unexpected error:', error);
    }
  }
  
  // Example 2: Clean calculator
  console.log('Example 2: OrderCalculator');
  const calculator = new OrderCalculator();
  const order: Order = {
    id: 'order1',
    userId: 'user123',
    status: 'pending',
    items: [
      { productId: 'prod1', quantity: 2, price: 10 },
      { productId: 'prod2', quantity: 1, price: 20 }
    ]
  };
  
  const total = calculator.calculateTotal(order);
  console.log(`Order total: $${total}`);
  console.log('\nImprovements:');
  console.log('- Focused responsibility (only calculations)');
  console.log('- Clear method names');
  console.log('- No hidden dependencies\n');
  
  console.log('=== Key Improvements ===');
  console.log('1. Can explain each function in one sentence');
  console.log('2. Variables declared close to use');
  console.log('3. No duplication, extracted patterns');
  console.log('4. Short functions, linear flow');
  console.log('5. Validation at API boundaries');
  console.log('6. Consistent error model');
  console.log('7. Explicit, injectable dependencies');
}

if (require.main === module) {
  runAfterExample().catch(console.error);
}

export { runAfterExample };
