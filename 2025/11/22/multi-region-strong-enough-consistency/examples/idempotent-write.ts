import { IdempotentWriteService, IdempotencyStore } from '../src/idempotent-write';

/**
 * Example: Idempotent write endpoint
 * 
 * Demonstrates how to handle duplicate requests safely
 * using idempotency keys
 */

async function main() {
  const store = new IdempotencyStore();
  const service = new IdempotentWriteService(store);

  // Payment processing handler
  const processPayment = async (data: any) => {
    console.log('Processing payment:', data);
    
    // Simulate payment processing
    await new Promise(resolve => setTimeout(resolve, 100));
    
    return {
      id: `payment-${Date.now()}`,
      amount: data.amount,
      currency: data.currency,
      status: 'completed',
      timestamp: new Date()
    };
  };

  const request = {
    idempotencyKey: 'payment-123-abc',
    operation: 'create_payment',
    data: {
      amount: 100,
      currency: 'USD'
    }
  };

  console.log('\n=== First Request ===');
  const result1 = await service.processWrite(request, processPayment);
  console.log('Result:', result1);

  console.log('\n=== Duplicate Request (same key) ===');
  const result2 = await service.processWrite(request, processPayment);
  console.log('Result (cached):', result2);
  console.log('Same payment ID:', result1.id === result2.id);

  console.log('\n=== Different Request (different key) ===');
  const differentRequest = {
    ...request,
    idempotencyKey: 'payment-456-def'
  };
  const result3 = await service.processWrite(differentRequest, processPayment);
  console.log('Result (new):', result3);
  console.log('Different payment ID:', result1.id !== result3.id);
}

main().catch(console.error);

