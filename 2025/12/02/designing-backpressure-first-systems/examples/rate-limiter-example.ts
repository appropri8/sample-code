/**
 * Rate Limiter Example
 * 
 * Demonstrates token bucket and leaky bucket rate limiters.
 */

import { TokenBucket, LeakyBucket, PerClientRateLimiter } from '../src/rate-limiter';

console.log('=== Token Bucket Example ===');

const tokenBucket = new TokenBucket(10, 5); // 10 tokens, refill 5 per second

console.log('Initial tokens:', tokenBucket.getTokens());

// Consume 10 tokens quickly
for (let i = 0; i < 10; i++) {
  const allowed = tokenBucket.tryConsume();
  console.log(`Request ${i + 1}: ${allowed ? 'allowed' : 'rejected'}, tokens: ${tokenBucket.getTokens()}`);
}

// Try one more (should be rejected)
const allowed = tokenBucket.tryConsume();
console.log(`Request 11: ${allowed ? 'allowed' : 'rejected'}, tokens: ${tokenBucket.getTokens()}`);

// Wait and check wait time
const waitTime = tokenBucket.getWaitTime();
console.log(`Wait time for next token: ${waitTime}ms`);

console.log('\n=== Leaky Bucket Example ===');

const leakyBucket = new LeakyBucket(5, 2); // Capacity 5, leak 2 per second

// Add 5 requests
for (let i = 0; i < 5; i++) {
  const allowed = leakyBucket.tryAdd();
  console.log(`Request ${i + 1}: ${allowed ? 'allowed' : 'rejected'}, queue size: ${leakyBucket.getQueueSize()}`);
}

// Try one more (should be rejected)
const allowed2 = leakyBucket.tryAdd();
console.log(`Request 6: ${allowed2 ? 'allowed' : 'rejected'}, queue size: ${leakyBucket.getQueueSize()}`);

const waitTime2 = leakyBucket.getWaitTime();
console.log(`Wait time: ${waitTime2}ms`);

console.log('\n=== Per-Client Rate Limiter Example ===');

const perClientLimiter = new PerClientRateLimiter(5, 5); // 5 tokens, refill 5 per second

const client1 = 'user-123';
const client2 = 'user-456';

console.log(`Client ${client1}:`);
for (let i = 0; i < 7; i++) {
  const allowed = perClientLimiter.allow(client1);
  console.log(`  Request ${i + 1}: ${allowed ? 'allowed' : 'rejected'}`);
}

console.log(`Client ${client2}:`);
for (let i = 0; i < 7; i++) {
  const allowed = perClientLimiter.allow(client2);
  console.log(`  Request ${i + 1}: ${allowed ? 'allowed' : 'rejected'}`);
}

