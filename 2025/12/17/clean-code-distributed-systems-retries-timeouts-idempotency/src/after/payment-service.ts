/**
 * AFTER: Clean payment service
 * 
 * Improvements:
 * - Policy defined separately
 * - Reliability logic separated from business logic
 * - Behavior is visible from function signature
 * - Easy to test
 * - Easy to change policies
 */

import { callWithTimeout, retry } from '../resilience';
import { ChargeRequest, ChargeResult, HttpError, isRetryableError } from '../types';

// Policy definition - one place to define behavior
const HTTP_POLICIES = {
  payment: {
    timeoutMs: 5000,
    retry: {
      maxAttempts: 3,
      shouldRetry: isRetryableError,
      backoffMs: 1000
    }
  }
};

/**
 * Generic HTTP call wrapper that applies policies
 */
async function callHttpWithPolicy<T>(
  service: keyof typeof HTTP_POLICIES,
  call: () => Promise<T>
): Promise<T> {
  const policy = HTTP_POLICIES[service];
  if (!policy) {
    throw new Error(`No policy defined for service: ${service}`);
  }

  return await retry(
    () => callWithTimeout(call, { timeoutMs: policy.timeoutMs }),
    {
      ...policy.retry,
      onRetry: (attempt, error) => {
        console.log(`Retrying ${service} call (attempt ${attempt}):`, error.message);
      }
    }
  );
}

export class PaymentService {
  private async callPaymentApi(request: ChargeRequest): Promise<ChargeResult> {
    // Simulated API call - pure business logic
    return new Promise((resolve, reject) => {
      setTimeout(() => {
        if (Math.random() > 0.3) {
          resolve({
            transactionId: `tx-${Date.now()}`,
            amount: request.amount,
            status: 'success'
          });
        } else {
          const error: HttpError = {
            name: 'HttpError',
            message: 'Service unavailable',
            statusCode: 503
          };
          reject(error);
        }
      }, 2000);
    });
  }

  /**
   * Charge customer - clean and readable
   * You can see from the function that it:
   * - Uses the payment policy (5s timeout, 3 retries)
   * - Calls the payment API
   * - Returns a ChargeResult
   */
  async chargeCustomer(amount: number, customerId: string): Promise<ChargeResult> {
    return await callHttpWithPolicy('payment', () =>
      this.callPaymentApi({ amount, customerId })
    );
  }
}
