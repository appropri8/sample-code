/**
 * Per-tenant rate limiting.
 * 
 * This module demonstrates rate limiting that is scoped per tenant,
 * not globally. Different tenant tiers can have different limits.
 */

import Redis from 'ioredis';
import { TenantContext } from './types';

/**
 * Rate limiter that tracks limits per tenant.
 */
export class PerTenantRateLimiter {
  private redis: Redis;
  private defaultLimit: number;
  
  constructor(redis: Redis, defaultLimit: number = 100) {
    this.redis = redis;
    this.defaultLimit = defaultLimit;
  }
  
  /**
   * Check if request is allowed for tenant.
   * Returns true if allowed, false if rate limited.
   */
  async allow(tenantId: string, limit?: number): Promise<boolean> {
    const key = `rate_limit:${tenantId}`;
    const window = 60; // 1 minute window
    const actualLimit = limit || this.defaultLimit;
    
    // Get current count
    const current = await this.redis.get(key);
    const count = current ? parseInt(current, 10) : 0;
    
    if (count >= actualLimit) {
      return false;
    }
    
    // Increment counter
    const newCount = await this.redis.incr(key);
    
    // Set expiry on first request in window
    if (newCount === 1) {
      await this.redis.expire(key, window);
    }
    
    return true;
  }
  
  /**
   * Get remaining requests for tenant in current window.
   */
  async getRemaining(tenantId: string, limit?: number): Promise<number> {
    const key = `rate_limit:${tenantId}`;
    const actualLimit = limit || this.defaultLimit;
    const current = await this.redis.get(key);
    const count = current ? parseInt(current, 10) : 0;
    return Math.max(0, actualLimit - count);
  }
  
  /**
   * Get time until rate limit resets (in seconds).
   */
  async getResetTime(tenantId: string): Promise<number> {
    const key = `rate_limit:${tenantId}`;
    const ttl = await this.redis.ttl(key);
    return ttl > 0 ? ttl : 0;
  }
}

/**
 * Rate limiter that uses tenant context to determine limits.
 */
export class TenantAwareRateLimiter {
  private limiter: PerTenantRateLimiter;
  
  constructor(redis: Redis) {
    this.limiter = new PerTenantRateLimiter(redis);
  }
  
  /**
   * Check if request is allowed based on tenant tier.
   */
  async allow(tenant: TenantContext): Promise<boolean> {
    const limit = tenant.rateLimitPerMinute;
    return this.limiter.allow(tenant.tenantId, limit);
  }
  
  /**
   * Get rate limit info for tenant.
   */
  async getRateLimitInfo(tenant: TenantContext): Promise<{
    allowed: boolean;
    remaining: number;
    resetIn: number;
    limit: number;
  }> {
    const limit = tenant.rateLimitPerMinute;
    const allowed = await this.limiter.allow(tenant.tenantId, limit);
    const remaining = await this.limiter.getRemaining(tenant.tenantId, limit);
    const resetIn = await this.limiter.getResetTime(tenant.tenantId);
    
    return {
      allowed,
      remaining,
      resetIn,
      limit
    };
  }
}

/**
 * In-memory rate limiter (for testing or small deployments).
 */
export class InMemoryPerTenantRateLimiter {
  private counters = new Map<string, { count: number; resetAt: number }>();
  private defaultLimit: number;
  
  constructor(defaultLimit: number = 100) {
    this.defaultLimit = defaultLimit;
  }
  
  allow(tenantId: string, limit?: number): boolean {
    const actualLimit = limit || this.defaultLimit;
    const now = Date.now();
    const window = 60000; // 1 minute
    
    const counter = this.counters.get(tenantId);
    
    if (!counter || now > counter.resetAt) {
      // New window
      this.counters.set(tenantId, { count: 1, resetAt: now + window });
      return true;
    }
    
    if (counter.count >= actualLimit) {
      return false;
    }
    
    counter.count++;
    return true;
  }
  
  getRemaining(tenantId: string, limit?: number): number {
    const actualLimit = limit || this.defaultLimit;
    const counter = this.counters.get(tenantId);
    
    if (!counter || Date.now() > counter.resetAt) {
      return actualLimit;
    }
    
    return Math.max(0, actualLimit - counter.count);
  }
  
  getResetTime(tenantId: string): number {
    const counter = this.counters.get(tenantId);
    if (!counter) {
      return 0;
    }
    
    const remaining = counter.resetAt - Date.now();
    return Math.max(0, Math.ceil(remaining / 1000));
  }
}

