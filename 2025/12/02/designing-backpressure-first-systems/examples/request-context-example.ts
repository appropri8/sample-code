/**
 * Request Context Example
 * 
 * Demonstrates request context with timeouts and cancellation.
 */

import { RequestContext, createAbortSignal } from '../src/request-context';

console.log('=== Request Context Example ===');

// Create a context with 5 second timeout
const context = new RequestContext(5000);

console.log('Context created with 5 second timeout');
console.log('Remaining time:', context.getRemainingTime(), 'ms');
console.log('Is expired:', context.isExpired());

// Simulate a long-running operation
async function longRunningOperation(context: RequestContext): Promise<string> {
  console.log('Starting long-running operation...');
  
  for (let i = 0; i < 10; i++) {
    if (context.isExpired()) {
      throw new Error('Operation cancelled: timeout exceeded');
    }
    
    console.log(`  Step ${i + 1}/10, remaining: ${context.getRemainingTime()}ms`);
    await new Promise(resolve => setTimeout(resolve, 1000));
  }
  
  return 'Operation completed';
}

// Try to run the operation
try {
  const result = await longRunningOperation(context);
  console.log('Result:', result);
} catch (error) {
  console.log('Error:', (error as Error).message);
}

// Example with AbortSignal
console.log('\n=== AbortSignal Example ===');

const context2 = new RequestContext(2000);
const signal = createAbortSignal(context2);

async function fetchWithTimeout(url: string, signal: AbortSignal): Promise<Response> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 2000);
  
  // Combine signals
  signal.addEventListener('abort', () => controller.abort());
  
  try {
    // Simulate fetch
    await new Promise((resolve, reject) => {
      const checkAbort = () => {
        if (signal.aborted || controller.signal.aborted) {
          clearTimeout(timeoutId);
          reject(new Error('Request aborted'));
        } else {
          setTimeout(checkAbort, 100);
        }
      };
      checkAbort();
      
      // Simulate network delay
      setTimeout(() => {
        clearTimeout(timeoutId);
        if (!signal.aborted && !controller.signal.aborted) {
          resolve('Response');
        }
      }, 3000);
    });
    
    return {} as Response;
  } catch (error) {
    clearTimeout(timeoutId);
    throw error;
  }
}

try {
  console.log('Starting fetch with 2 second timeout...');
  await fetchWithTimeout('https://example.com', signal);
  console.log('Fetch completed');
} catch (error) {
  console.log('Fetch error:', (error as Error).message);
}

