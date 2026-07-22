export class CircuitBreaker {
  private failureCount = 0;
  private lastFailureTime: Date | null = null;
  private state: 'closed' | 'open' | 'half-open' = 'closed';

  constructor(
    private readonly threshold: number,
    private readonly cooldownMs: number
  ) {}

  allowRequest(): boolean {
    if (this.state === 'closed') {
      return true;
    }

    if (this.state === 'open') {
      if (this.lastFailureTime && Date.now() - this.lastFailureTime.getTime() > this.cooldownMs) {
        this.state = 'half-open';
        return true;
      }
      return false;
    }

    return true;
  }

  recordSuccess(): void {
    this.failureCount = 0;
    this.state = 'closed';
    this.lastFailureTime = null;
  }

  recordFailure(): void {
    this.failureCount += 1;
    this.lastFailureTime = new Date();

    if (this.failureCount >= this.threshold) {
      this.state = 'open';
    }
  }

  remainingCooldownMs(): number {
    if (this.state !== 'open' || !this.lastFailureTime) {
      return 0;
    }
    const elapsed = Date.now() - this.lastFailureTime.getTime();
    return Math.max(0, this.cooldownMs - elapsed);
  }

  reset(): void {
    this.failureCount = 0;
    this.state = 'closed';
    this.lastFailureTime = null;
  }
}