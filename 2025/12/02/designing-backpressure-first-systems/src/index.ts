/**
 * Main entry point demonstrating backpressure patterns.
 */

import express, { Request, Response } from 'express';
import { PerClientRateLimiter } from './rate-limiter';
import { ConcurrencyLimiter } from './concurrency-limiter';
import { BoundedQueue } from './bounded-queue';
import { WorkerPool, Job } from './worker-pool';
import { CircuitBreaker } from './circuit-breaker';
import { RequestContext } from './request-context';

const app = express();
app.use(express.json());

// Rate limiter: 10 requests per second per client
const rateLimiter = new PerClientRateLimiter(10, 10);

// Concurrency limiter: max 50 concurrent requests
const concurrencyLimiter = new ConcurrencyLimiter(50);

// Bounded queue: max 200 jobs
const jobQueue = new BoundedQueue<Job>(200);

// Worker pool: 10 workers
const workerPool = new WorkerPool(10, 200);
workerPool.start();

// Circuit breaker for external service
const paymentCircuitBreaker = new CircuitBreaker(5, 60000, 3);

/**
 * Example job implementation.
 */
class OrderJob implements Job {
  constructor(
    private orderId: string,
    private userId: string,
    private amount: number
  ) {}

  async execute(): Promise<void> {
    console.log(`Processing order ${this.orderId} for user ${this.userId}`);
    
    // Simulate work
    await new Promise(resolve => setTimeout(resolve, 100));
    
    // Simulate external API call with circuit breaker
    await paymentCircuitBreaker.execute(async () => {
      // Simulate payment processing
      await new Promise(resolve => setTimeout(resolve, 50));
      if (Math.random() < 0.1) {
        throw new Error('Payment service error');
      }
    });
    
    console.log(`Order ${this.orderId} processed successfully`);
  }

  async handleError(error: Error): Promise<void> {
    console.error(`Order ${this.orderId} failed:`, error.message);
    // In real implementation, you might:
    // - Send notification to user
    // - Log to error tracking service
    // - Retry with exponential backoff
  }
}

/**
 * Health check endpoint.
 */
app.get('/health', (req: Request, res: Response) => {
  res.json({ status: 'ok' });
});

/**
 * Order endpoint with backpressure.
 */
app.post('/api/orders', async (req: Request, res: Response) => {
  const userId = req.headers['x-user-id'] as string || 'anonymous';
  const { orderId, amount } = req.body;

  // Rate limiting
  if (!rateLimiter.allow(userId)) {
    const waitTime = rateLimiter.getWaitTime(userId);
    return res.status(429)
              .setHeader('Retry-After', Math.ceil(waitTime / 1000))
              .json({ 
                error: 'Rate limit exceeded',
                retryAfter: Math.ceil(waitTime / 1000)
              });
  }

  // Check queue capacity
  if (jobQueue.isFull) {
    return res.status(503)
              .setHeader('Retry-After', '10')
              .json({ 
                error: 'Service overloaded',
                retryAfter: 10
              });
  }

  // Enqueue with concurrency limit
  try {
    await concurrencyLimiter.execute(async () => {
      const job = new OrderJob(orderId, userId, amount);
      if (!jobQueue.enqueue(job)) {
        throw new Error('Queue full');
      }
      await workerPool.submit(job);
    });

    res.status(202).json({ 
      message: 'Order queued',
      orderId,
      queueSize: jobQueue.size
    });
  } catch (error) {
    res.status(503).json({ 
      error: 'Service overloaded',
      message: (error as Error).message
    });
  }
});

/**
 * Metrics endpoint.
 */
app.get('/api/metrics', (req: Request, res: Response) => {
  res.json({
    queueSize: jobQueue.size,
    queueFull: jobQueue.isFull,
    activeConcurrency: concurrencyLimiter.getActiveCount(),
    queuedConcurrency: concurrencyLimiter.getQueueSize(),
    circuitBreakerState: paymentCircuitBreaker.getState(),
    circuitBreakerFailures: paymentCircuitBreaker.getFailureCount()
  });
});

const PORT = process.env.PORT || 3000;

app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
  console.log(`Health check: http://localhost:${PORT}/health`);
  console.log(`Metrics: http://localhost:${PORT}/api/metrics`);
});

// Graceful shutdown
process.on('SIGTERM', async () => {
  console.log('SIGTERM received, shutting down gracefully...');
  await workerPool.stop();
  process.exit(0);
});

