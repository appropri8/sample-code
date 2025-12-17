/**
 * Example: HTTP call with retries and timeouts
 * 
 * Demonstrates the clean pattern for outbound HTTP calls
 */

import { PaymentService } from '../after/payment-service';

async function main() {
  const paymentService = new PaymentService();

  try {
    console.log('Charging customer...');
    const result = await paymentService.chargeCustomer(100.50, 'customer-123');
    console.log('Charge successful:', result);
  } catch (error) {
    console.error('Charge failed:', error);
  }
}

if (require.main === module) {
  main().catch(console.error);
}
