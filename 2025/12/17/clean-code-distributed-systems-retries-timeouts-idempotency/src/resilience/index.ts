/**
 * Resilience primitives for distributed systems
 * 
 * Three clean primitives:
 * 1. callWithTimeout - Makes timeouts explicit
 * 2. retry - Makes retry behavior visible
 * 3. ensureIdempotent - Makes idempotency explicit
 */

export * from './timeout';
export * from './retry';
export * from './idempotency';
