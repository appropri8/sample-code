// Complete BEFORE example: Messy AI-generated code
// This demonstrates all the problems discussed in the article

import { processUserOrder } from '../before/order-processor';
import { handleUserRequest } from '../before/user-handler';

// Example usage of messy code
async function runBeforeExample() {
  console.log('=== BEFORE: Messy AI-Generated Code ===\n');
  
  // Example 1: Generic function with nested conditionals
  console.log('Example 1: processUserOrder');
  const result1 = processUserOrder({
    user: { id: 'user123' }
  });
  console.log('Result:', JSON.stringify(result1, null, 2));
  console.log('\nProblems:');
  console.log('- Generic names (processUserOrder, data, result)');
  console.log('- Deep nesting (4-5 levels)');
  console.log('- Mixed validation and processing');
  console.log('- Inconsistent error handling');
  console.log('- Hidden dependencies (getUserData)\n');
  
  // Example 2: Generic handler pattern
  console.log('Example 2: handleUserRequest');
  const result2 = handleUserRequest({
    userId: 'user123',
    action: 'getOrders'
  });
  console.log('Result:', JSON.stringify(result2, null, 2));
  console.log('\nProblems:');
  console.log('- Generic handler name');
  console.log('- Deep nesting with early returns missing');
  console.log('- Mixed concerns (validation + processing)');
  console.log('- Hard to test (hidden dependencies)\n');
  
  console.log('=== Key Issues ===');
  console.log('1. Can\'t explain what functions do in one sentence');
  console.log('2. Variables declared far from use');
  console.log('3. Repeated validation patterns');
  console.log('4. Functions too long, too nested');
  console.log('5. Validation in business logic');
  console.log('6. Inconsistent error handling');
  console.log('7. Hidden global dependencies');
}

if (require.main === module) {
  runBeforeExample().catch(console.error);
}

export { runBeforeExample };
