/**
 * Circuit Breaker Example
 * 
 * Demonstrates circuit breaker pattern for protecting external dependencies.
 */

import { CircuitBreaker, CircuitState } from '../src/circuit-breaker';

console.log('=== Circuit Breaker Example ===');

const circuitBreaker = new CircuitBreaker(3, 5000, 2); // 3 failures to open, 5s timeout, 2 half-open calls

// Simulate a flaky external service
let callCount = 0;
async function flakyService(): Promise<string> {
  callCount++;
  // Fail first 5 calls, then succeed
  if (callCount <= 5) {
    throw new Error('Service error');
  }
  return 'Success';
}

console.log('Initial state:', circuitBreaker.getState());

// Make calls that will fail
for (let i = 0; i < 5; i++) {
  try {
    await circuitBreaker.execute(flakyService);
    console.log(`Call ${i + 1}: Success`);
  } catch (error) {
    console.log(`Call ${i + 1}: ${(error as Error).message}, State: ${circuitBreaker.getState()}, Failures: ${circuitBreaker.getFailureCount()}`);
  }
}

// Circuit should be open now
console.log('\nCircuit state after failures:', circuitBreaker.getState());

// Try to call while circuit is open
try {
  await circuitBreaker.execute(flakyService);
} catch (error) {
  console.log(`Call while open: ${(error as Error).message}`);
}

// Wait for timeout
console.log('\nWaiting for timeout...');
await new Promise(resolve => setTimeout(resolve, 6000));

// Circuit should be half-open now
console.log('Circuit state after timeout:', circuitBreaker.getState());

// Try calls in half-open state
for (let i = 0; i < 3; i++) {
  try {
    const result = await circuitBreaker.execute(flakyService);
    console.log(`Half-open call ${i + 1}: ${result}, State: ${circuitBreaker.getState()}`);
  } catch (error) {
    console.log(`Half-open call ${i + 1}: ${(error as Error).message}, State: ${circuitBreaker.getState()}`);
  }
}

// Circuit should be closed now
console.log('\nFinal circuit state:', circuitBreaker.getState());

