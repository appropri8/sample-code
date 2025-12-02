/**
 * Example: Per-tenant rate limiting.
 * 
 * Demonstrates rate limiting that is scoped per tenant,
 * with different limits for different tenant tiers.
 */

import Redis from 'ioredis';
import {
  PerTenantRateLimiter,
  TenantAwareRateLimiter,
  InMemoryPerTenantRateLimiter
} from '../src/rate-limiter';
import { TenantContext } from '../src/types';

// Mock tenant contexts
const tenant1: TenantContext = {
  tenantId: 'tenant-1',
  tier: 'enterprise',
  features: ['feature-a', 'feature-b'],
  rateLimitPerMinute: 10000,
  quotaLimits: {
    requestsPerMinute: 10000,
    jobsPerMinute: 1000,
    storageBytes: 1000000000,
    queryCostPerMonth: 1000
  }
};

const tenant2: TenantContext = {
  tenantId: 'tenant-2',
  tier: 'standard',
  features: ['feature-a'],
  rateLimitPerMinute: 1000,
  quotaLimits: {
    requestsPerMinute: 1000,
    jobsPerMinute: 100,
    storageBytes: 100000000,
    queryCostPerMonth: 100
  }
};

const tenant3: TenantContext = {
  tenantId: 'tenant-3',
  tier: 'free',
  features: [],
  rateLimitPerMinute: 100,
  quotaLimits: {
    requestsPerMinute: 100,
    jobsPerMinute: 10,
    storageBytes: 10000000,
    queryCostPerMonth: 10
  }
};

async function demonstrateRateLimiting() {
  console.log('=== Per-Tenant Rate Limiting Example ===\n');
  
  // Example 1: In-memory rate limiter (for testing)
  console.log('1. In-Memory Rate Limiter:');
  const inMemoryLimiter = new InMemoryPerTenantRateLimiter(100);
  
  // Simulate requests for tenant-1
  console.log('   Tenant-1 (limit: 100/min):');
  for (let i = 0; i < 5; i++) {
    const allowed = inMemoryLimiter.allow('tenant-1', 100);
    const remaining = inMemoryLimiter.getRemaining('tenant-1', 100);
    console.log(`   Request ${i + 1}: ${allowed ? 'allowed' : 'blocked'}, remaining: ${remaining}`);
  }
  console.log('');
  
  // Example 2: Redis-based rate limiter
  console.log('2. Redis-Based Rate Limiter:');
  try {
    const redis = new Redis({
      host: process.env.REDIS_HOST || 'localhost',
      port: parseInt(process.env.REDIS_PORT || '6379')
    });
    
    const redisLimiter = new PerTenantRateLimiter(redis, 100);
    
    // Check rate limit for tenant-1
    const allowed = await redisLimiter.allow('tenant-1', 100);
    const remaining = await redisLimiter.getRemaining('tenant-1', 100);
    const resetIn = await redisLimiter.getResetTime('tenant-1');
    
    console.log(`   Tenant-1: ${allowed ? 'allowed' : 'blocked'}`);
    console.log(`   Remaining: ${remaining}`);
    console.log(`   Reset in: ${resetIn}s\n`);
    
    await redis.quit();
  } catch (error: any) {
    console.log('   Error (Redis not running):', error.message);
    console.log('   Start Redis to test Redis-based limiter\n');
  }
  
  // Example 3: Tenant-aware rate limiter (uses tenant context)
  console.log('3. Tenant-Aware Rate Limiter:');
  console.log('   Different limits for different tenant tiers\n');
  
  const tenantAwareLimiter = new TenantAwareRateLimiter(
    new Redis({ host: 'localhost', port: 6379 })
  );
  
  try {
    // Enterprise tenant (high limit)
    const info1 = await tenantAwareLimiter.getRateLimitInfo(tenant1);
    console.log(`   ${tenant1.tenantId} (${tenant1.tier}):`);
    console.log(`     Limit: ${info1.limit}/min`);
    console.log(`     Remaining: ${info1.remaining}`);
    console.log(`     Reset in: ${info1.resetIn}s\n`);
    
    // Standard tenant (medium limit)
    const info2 = await tenantAwareLimiter.getRateLimitInfo(tenant2);
    console.log(`   ${tenant2.tenantId} (${tenant2.tier}):`);
    console.log(`     Limit: ${info2.limit}/min`);
    console.log(`     Remaining: ${info2.remaining}`);
    console.log(`     Reset in: ${info2.resetIn}s\n`);
    
    // Free tenant (low limit)
    const info3 = await tenantAwareLimiter.getRateLimitInfo(tenant3);
    console.log(`   ${tenant3.tenantId} (${tenant3.tier}):`);
    console.log(`     Limit: ${info3.limit}/min`);
    console.log(`     Remaining: ${info3.remaining}`);
    console.log(`     Reset in: ${info3.resetIn}s\n`);
  } catch (error: any) {
    console.log('   Error (Redis not running):', error.message);
    console.log('   Using in-memory limiter for demonstration:\n');
    
    const inMemoryTenantLimiter = new InMemoryPerTenantRateLimiter();
    
    // Simulate different tenant tiers
    console.log(`   ${tenant1.tenantId} (${tenant1.tier}):`);
    for (let i = 0; i < 3; i++) {
      const allowed = inMemoryTenantLimiter.allow(tenant1.tenantId, tenant1.rateLimitPerMinute);
      const remaining = inMemoryTenantLimiter.getRemaining(tenant1.tenantId, tenant1.rateLimitPerMinute);
      console.log(`     Request ${i + 1}: ${allowed ? 'allowed' : 'blocked'}, remaining: ${remaining}`);
    }
    console.log('');
    
    console.log(`   ${tenant3.tenantId} (${tenant3.tier}):`);
    for (let i = 0; i < 3; i++) {
      const allowed = inMemoryTenantLimiter.allow(tenant3.tenantId, tenant3.rateLimitPerMinute);
      const remaining = inMemoryTenantLimiter.getRemaining(tenant3.tenantId, tenant3.rateLimitPerMinute);
      console.log(`     Request ${i + 1}: ${allowed ? 'allowed' : 'blocked'}, remaining: ${remaining}`);
    }
    console.log('');
  }
  
  console.log('=== Key Points ===');
  console.log('- Rate limits are per tenant, not global');
  console.log('- Different tenant tiers have different limits');
  console.log('- Use Redis for distributed rate limiting');
  console.log('- Use in-memory for single-server deployments');
  console.log('- Return 429 status with Retry-After header when limited');
}

// Run example
demonstrateRateLimiting().catch(console.error);

