/**
 * Concurrency Limiter
 * 
 * Limits the number of concurrent operations.
 * Queues excess operations until capacity is available.
 */
export class ConcurrencyLimiter {
  private active = 0;
  private queue: Array<() => void> = [];

  constructor(private maxConcurrency: number) {
    if (maxConcurrency <= 0) {
      throw new Error('Max concurrency must be greater than 0');
    }
  }

  /**
   * Execute a function with concurrency limiting.
   */
  async execute<T>(fn: () => Promise<T>): Promise<T> {
    if (this.active < this.maxConcurrency) {
      this.active++;
      try {
        return await fn();
      } finally {
        this.active--;
        this.processQueue();
      }
    }

    return new Promise<T>((resolve, reject) => {
      const executeQueued = async () => {
        // Re-check capacity before executing to prevent race condition
        // Between scheduling with setImmediate and execution, other operations
        // may have started, so we must verify capacity is still available
        if (this.active >= this.maxConcurrency) {
          // Re-queue at front to try again later
          this.queue.unshift(executeQueued);
          this.processQueue();
          return;
        }
        
        this.active++;
        try {
          const result = await fn();
          resolve(result);
        } catch (error) {
          reject(error);
        } finally {
          this.active--;
          this.processQueue();
        }
      };
      
      this.queue.push(executeQueued);
      this.processQueue();
    });
  }

  /**
   * Process the next item in the queue if capacity is available.
   */
  private processQueue() {
    if (this.queue.length > 0 && this.active < this.maxConcurrency) {
      const next = this.queue.shift();
      if (next) {
        // Execute asynchronously to avoid stack overflow
        setImmediate(() => next());
      }
    }
  }

  /**
   * Get the number of active operations.
   */
  getActiveCount(): number {
    return this.active;
  }

  /**
   * Get the number of queued operations.
   */
  getQueueSize(): number {
    return this.queue.length;
  }

  /**
   * Check if the limiter is at capacity.
   */
  isAtCapacity(): boolean {
    return this.active >= this.maxConcurrency;
  }
}

