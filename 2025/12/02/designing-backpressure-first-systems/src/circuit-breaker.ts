/**
 * Circuit Breaker States
 */
export enum CircuitState {
  CLOSED = 'CLOSED',
  OPEN = 'OPEN',
  HALF_OPEN = 'HALF_OPEN'
}

/**
 * Circuit Breaker
 * 
 * Prevents cascading failures by stopping calls to failing dependencies.
 * 
 * - CLOSED: Normal operation, calls pass through
 * - OPEN: Calls fail fast, no calls to dependency
 * - HALF_OPEN: Testing if dependency recovered, allows limited calls
 */
export class CircuitBreaker {
  private state = CircuitState.CLOSED;
  private failures = 0;
  private lastFailureTime = 0;
  private halfOpenCalls = 0;

  constructor(
    private failureThreshold: number = 5,
    private timeout: number = 60000, // 60 seconds
    private halfOpenMaxCalls: number = 3
  ) {}

  /**
   * Execute a function with circuit breaker protection.
   */
  async execute<T>(fn: () => Promise<T>): Promise<T> {
    if (this.state === CircuitState.OPEN) {
      if (Date.now() - this.lastFailureTime > this.timeout) {
        // Transition to half-open
        this.state = CircuitState.HALF_OPEN;
        this.failures = 0;
        this.halfOpenCalls = 0;
      } else {
        throw new Error('Circuit breaker is open');
      }
    }

    if (this.state === CircuitState.HALF_OPEN) {
      if (this.halfOpenCalls >= this.halfOpenMaxCalls) {
        throw new Error('Circuit breaker half-open limit reached');
      }
      this.halfOpenCalls++;
    }

    try {
      const result = await fn();
      this.onSuccess();
      return result;
    } catch (error) {
      this.onFailure();
      throw error;
    }
  }

  /**
   * Handle successful call.
   */
  private onSuccess() {
    this.failures = 0;
    if (this.state === CircuitState.HALF_OPEN) {
      this.state = CircuitState.CLOSED;
      this.halfOpenCalls = 0;
    }
  }

  /**
   * Handle failed call.
   */
  private onFailure() {
    this.failures++;
    this.lastFailureTime = Date.now();

    if (this.state === CircuitState.HALF_OPEN) {
      // Half-open test failed, open the circuit
      this.state = CircuitState.OPEN;
      this.halfOpenCalls = 0;
    } else if (this.failures >= this.failureThreshold) {
      // Too many failures, open the circuit
      this.state = CircuitState.OPEN;
    }
  }

  /**
   * Get current circuit state.
   */
  getState(): CircuitState {
    return this.state;
  }

  /**
   * Get failure count.
   */
  getFailureCount(): number {
    return this.failures;
  }

  /**
   * Reset the circuit breaker to closed state.
   */
  reset() {
    this.state = CircuitState.CLOSED;
    this.failures = 0;
    this.lastFailureTime = 0;
    this.halfOpenCalls = 0;
  }
}

