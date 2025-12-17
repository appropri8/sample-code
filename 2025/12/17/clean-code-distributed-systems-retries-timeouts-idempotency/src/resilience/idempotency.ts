/**
 * Idempotency wrapper for command operations
 * Makes idempotency explicit and visible
 */

export interface IdempotencyStore {
  get<T>(key: string): Promise<T | null>;
  set<T>(key: string, value: T, ttlSeconds?: number): Promise<void>;
}

export interface IdempotencyOptions {
  idempotencyKey: string;
  idempotencyStore: IdempotencyStore;
  ttlSeconds?: number; // Time to live for stored results
}

export class DuplicateRequestError extends Error {
  constructor(key: string) {
    super(`Duplicate request detected for key: ${key}`);
    this.name = 'DuplicateRequestError';
  }
}

/**
 * Ensures an operation is idempotent by checking for duplicate requests
 * 
 * @param fn - The function to execute (must be idempotent)
 * @param options - Idempotency configuration
 * @returns The result of the function, or cached result if duplicate
 * 
 * @example
 * ```typescript
 * const order = await ensureIdempotent(
 *   () => createOrder(userId, items),
 *   {
 *     idempotencyKey: `order-${userId}-${Date.now()}`,
 *     idempotencyStore: redisClient
 *   }
 * );
 * ```
 */
export async function ensureIdempotent<T>(
  fn: () => Promise<T>,
  options: IdempotencyOptions
): Promise<T> {
  const { idempotencyKey, idempotencyStore, ttlSeconds = 3600 } = options;

  // Check if we've already processed this request
  const existing = await idempotencyStore.get<T>(idempotencyKey);
  if (existing !== null) {
    return existing;
  }

  // Execute the operation
  const result = await fn();

  // Store the result
  await idempotencyStore.set(idempotencyKey, result, ttlSeconds);

  return result;
}
