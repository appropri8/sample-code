/**
 * BEFORE: Messy payment service
 * 
 * Problems:
 * - Retry logic mixed with business logic
 * - Timeout handling hidden inside
 * - No clear policy definition
 * - Hard to test
 * - Hard to change retry behavior
 */

export class PaymentService {
  async chargeCustomer(amount: number, customerId: string): Promise<any> {
    let lastError: any;
    const maxRetries = 3;
    const timeout = 5000;

    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        // Timeout logic mixed in
        const timeoutPromise = new Promise((_, reject) => {
          setTimeout(() => reject(new Error('Timeout')), timeout);
        });

        const chargePromise = this.callPaymentApi(amount, customerId);
        
        const result = await Promise.race([chargePromise, timeoutPromise]);
        
        // Business logic mixed with retry logic
        if (result && result.status === 'success') {
          return result;
        }
        
        throw new Error('Payment failed');
      } catch (error: any) {
        lastError = error;
        
        // Retry logic scattered
        if (attempt < maxRetries) {
          if (error.statusCode === 503 || error.statusCode === 429 || 
              (error.statusCode >= 500 && error.statusCode < 600)) {
            await this.sleep(1000 * attempt);
            continue;
          }
        }
        
        throw error;
      }
    }

    throw lastError;
  }

  private async callPaymentApi(amount: number, customerId: string): Promise<any> {
    // Simulated API call
    return new Promise((resolve, reject) => {
      setTimeout(() => {
        if (Math.random() > 0.3) {
          resolve({ status: 'success', transactionId: 'tx-123' });
        } else {
          reject({ statusCode: 503, message: 'Service unavailable' });
        }
      }, 2000);
    });
  }

  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}
