/**
 * Retry wrapper with explicit rules
 * Makes retry behavior visible and configurable
 */

export interface RetryOptions {
  maxAttempts: number;
  shouldRetry: (error: Error) => boolean;
  backoffMs: number;
  onRetry?: (attempt: number, error: Error) => void;
}

export class MaxRetriesError extends Error {
  constructor(attempts: number, lastError: Error) {
    super(`Max retries (${attempts}) reached. Last error: ${lastError.message}`);
    this.name = 'MaxRetriesError';
    this.cause = lastError;
  }
}

/**
 * Sleep utility
 */
function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Wraps a function call with retry logic
 * 
 * @param fn - The function to retry
 * @param options - Retry configuration
 * @returns The result of the function, or throws MaxRetriesError
 * 
 * @example
 * ```typescript
 * const result = await retry(
 *   () => callWithTimeout(() => paymentService.charge(amount), { timeoutMs: 5000 }),
 *   {
 *     maxAttempts: 3,
 *     shouldRetry: (error) => error.statusCode === 503 || error.statusCode === 429,
 *     backoffMs: 1000
 *   }
 * );
 * ```
 */
export async function retry<T>(
  fn: () => Promise<T>,
  options: RetryOptions
): Promise<T> {
  const { maxAttempts, shouldRetry, backoffMs, onRetry } = options;
  let lastError: Error;

  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error instanceof Error ? error : new Error(String(error));

      // Don't retry if we've reached max attempts
      if (attempt === maxAttempts) {
        throw new MaxRetriesError(maxAttempts, lastError);
      }

      // Don't retry if error is not retryable
      if (!shouldRetry(lastError)) {
        throw lastError;
      }

      // Log retry decision
      if (onRetry) {
        onRetry(attempt, lastError);
      }

      // Wait before retrying
      await sleep(backoffMs);
    }
  }

  // This should never be reached, but TypeScript needs it
  throw new MaxRetriesError(maxAttempts, lastError!);
}
