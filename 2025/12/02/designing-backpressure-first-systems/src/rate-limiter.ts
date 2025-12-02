/**
 * Token Bucket Rate Limiter
 * 
 * Implements a token bucket algorithm for rate limiting.
 * Each request consumes a token. Tokens refill at a fixed rate.
 */

export class TokenBucket {
  private tokens: number;
  private lastRefill: number;

  constructor(
    private capacity: number,
    private refillRate: number // tokens per second
  ) {
    this.tokens = capacity;
    this.lastRefill = Date.now();
  }

  /**
   * Try to consume a token. Returns true if allowed, false otherwise.
   */
  tryConsume(): boolean {
    this.refill();
    if (this.tokens >= 1) {
      this.tokens -= 1;
      return true;
    }
    return false;
  }

  /**
   * Refill tokens based on elapsed time.
   */
  private refill() {
    const now = Date.now();
    const elapsed = (now - this.lastRefill) / 1000;
    const tokensToAdd = elapsed * this.refillRate;
    this.tokens = Math.min(this.capacity, this.tokens + tokensToAdd);
    this.lastRefill = now;
  }

  /**
   * Get the wait time in milliseconds before the next token is available.
   */
  getWaitTime(): number {
    this.refill();
    if (this.tokens >= 1) return 0;
    const tokensNeeded = 1 - this.tokens;
    return Math.ceil(tokensNeeded / this.refillRate * 1000);
  }

  /**
   * Get current token count.
   */
  getTokens(): number {
    this.refill();
    return this.tokens;
  }
}

/**
 * Leaky Bucket Rate Limiter
 * 
 * Implements a leaky bucket algorithm for strict rate limiting.
 * Requests flow into a bucket that leaks at a fixed rate.
 */

export class LeakyBucket {
  private queue: number[] = [];

  constructor(
    private capacity: number,
    private leakRate: number // requests per second
  ) {}

  /**
   * Try to add a request. Returns true if allowed, false otherwise.
   */
  tryAdd(): boolean {
    this.leak();
    if (this.queue.length < this.capacity) {
      this.queue.push(Date.now());
      return true;
    }
    return false;
  }

  /**
   * Remove requests that have leaked out.
   */
  private leak() {
    const now = Date.now();
    const interval = 1000 / this.leakRate;
    while (this.queue.length > 0 && now - this.queue[0] >= interval) {
      this.queue.shift();
    }
  }

  /**
   * Get the wait time in milliseconds before the next request can be added.
   */
  getWaitTime(): number {
    this.leak();
    if (this.queue.length < this.capacity) return 0;
    const oldest = this.queue[0];
    const interval = 1000 / this.leakRate;
    return Math.ceil(interval - (Date.now() - oldest));
  }

  /**
   * Get current queue size.
   */
  getQueueSize(): number {
    this.leak();
    return this.queue.length;
  }
}

/**
 * Per-client rate limiter using token bucket.
 */
export class PerClientRateLimiter {
  private buckets: Map<string, TokenBucket> = new Map();

  constructor(
    private capacity: number,
    private refillRate: number
  ) {}

  /**
   * Check if a request from a client is allowed.
   */
  allow(clientId: string): boolean {
    if (!this.buckets.has(clientId)) {
      this.buckets.set(clientId, new TokenBucket(this.capacity, this.refillRate));
    }
    return this.buckets.get(clientId)!.tryConsume();
  }

  /**
   * Get wait time for a client.
   */
  getWaitTime(clientId: string): number {
    if (!this.buckets.has(clientId)) {
      return 0;
    }
    return this.buckets.get(clientId)!.getWaitTime();
  }

  /**
   * Check if a client is rate limited (read-only, doesn't consume tokens).
   */
  isRateLimited(clientId: string): boolean {
    if (!this.buckets.has(clientId)) {
      return false;
    }
    const bucket = this.buckets.get(clientId)!;
    // Check if tokens are available without consuming
    return bucket.getTokens() < 1;
  }
}

