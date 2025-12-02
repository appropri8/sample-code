/**
 * Request Context
 * 
 * Tracks request deadlines and cancellation state.
 * Propagates through the call stack to enable timeout and cancellation.
 */
export class RequestContext {
  private deadline: number;
  private cancelled = false;

  constructor(timeoutMs: number) {
    if (timeoutMs <= 0) {
      throw new Error('Timeout must be greater than 0');
    }
    this.deadline = Date.now() + timeoutMs;
  }

  /**
   * Check if the context has expired.
   */
  isExpired(): boolean {
    return Date.now() >= this.deadline || this.cancelled;
  }

  /**
   * Cancel the context.
   */
  cancel() {
    this.cancelled = true;
  }

  /**
   * Get the remaining time in milliseconds.
   */
  getRemainingTime(): number {
    return Math.max(0, this.deadline - Date.now());
  }

  /**
   * Get the deadline timestamp.
   */
  getDeadline(): number {
    return this.deadline;
  }

  /**
   * Check if the context is cancelled.
   */
  isCancelled(): boolean {
    return this.cancelled;
  }
}

/**
 * Helper function to create an AbortSignal from a RequestContext.
 */
export function createAbortSignal(context: RequestContext): AbortSignal {
  const controller = new AbortController();
  
  const checkExpiry = () => {
    if (context.isExpired()) {
      controller.abort();
    } else {
      const remaining = context.getRemainingTime();
      if (remaining > 0) {
        setTimeout(checkExpiry, Math.min(remaining, 1000));
      } else {
        controller.abort();
      }
    }
  };

  checkExpiry();
  return controller.signal;
}

/**
 * Helper function to sleep for a given number of milliseconds.
 */
export function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

