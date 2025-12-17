/**
 * Timeout wrapper for outbound calls
 * Makes timeouts explicit and visible
 */

export interface TimeoutOptions {
  timeoutMs: number;
}

export class TimeoutError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'TimeoutError';
  }
}

/**
 * Wraps a function call with a timeout
 * 
 * @param fn - The function to call
 * @param options - Timeout configuration
 * @returns The result of the function, or throws TimeoutError
 * 
 * @example
 * ```typescript
 * const result = await callWithTimeout(
 *   () => paymentService.charge(amount),
 *   { timeoutMs: 5000 }
 * );
 * ```
 */
export async function callWithTimeout<T>(
  fn: () => Promise<T>,
  options: TimeoutOptions
): Promise<T> {
  const { timeoutMs } = options;

  return Promise.race([
    fn(),
    new Promise<T>((_, reject) => {
      setTimeout(() => {
        reject(new TimeoutError(`Operation timed out after ${timeoutMs}ms`));
      }, timeoutMs);
    })
  ]);
}
