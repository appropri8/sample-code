/**
 * Worker Pool Example
 * 
 * Demonstrates bounded worker pool with job queue.
 */

import { WorkerPool, Job } from '../src/worker-pool';

console.log('=== Worker Pool Example ===');

const workerPool = new WorkerPool(3, 10); // 3 workers, queue size 10
workerPool.start();

class ExampleJob implements Job {
  constructor(private id: string, private duration: number) {}

  async execute(): Promise<void> {
    console.log(`[${new Date().toISOString()}] Job ${this.id} started`);
    await new Promise(resolve => setTimeout(resolve, this.duration));
    console.log(`[${new Date().toISOString()}] Job ${this.id} completed`);
  }

  async handleError(error: Error): Promise<void> {
    console.error(`Job ${this.id} failed:`, error.message);
  }
}

// Submit jobs
console.log('Submitting 15 jobs...');
for (let i = 1; i <= 15; i++) {
  try {
    const job = new ExampleJob(`job-${i}`, 1000);
    await workerPool.submit(job);
    console.log(`Job ${i} submitted, queue size: ${workerPool.getQueueSize()}`);
  } catch (error) {
    console.error(`Failed to submit job ${i}:`, (error as Error).message);
  }
}

// Wait for jobs to complete
console.log('\nWaiting for jobs to complete...');
await new Promise(resolve => setTimeout(resolve, 6000));

// Try to submit to full queue
console.log('\nFilling queue...');
for (let i = 16; i <= 25; i++) {
  try {
    const job = new ExampleJob(`job-${i}`, 1000);
    await workerPool.submit(job);
    console.log(`Job ${i} submitted`);
  } catch (error) {
    console.error(`Failed to submit job ${i}:`, (error as Error).message);
  }
}

// Wait a bit more
await new Promise(resolve => setTimeout(resolve, 2000));

// Stop worker pool
console.log('\nStopping worker pool...');
await workerPool.stop();
console.log('Worker pool stopped');

