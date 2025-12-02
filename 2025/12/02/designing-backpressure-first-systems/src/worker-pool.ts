import { BoundedQueue } from './bounded-queue';

/**
 * Job interface for worker pool.
 */
export interface Job {
  execute(): Promise<void>;
  handleError(error: Error): Promise<void>;
}

/**
 * Worker Pool
 * 
 * Manages a fixed number of workers that process jobs from a bounded queue.
 */
export class WorkerPool {
  private workers: Worker[] = [];
  private queue: BoundedQueue<Job>;
  private running = false;

  constructor(
    private numWorkers: number,
    queueSize: number
  ) {
    this.queue = new BoundedQueue(queueSize);
  }

  /**
   * Start the worker pool.
   */
  start() {
    if (this.running) return;
    this.running = true;
    this.startWorkers();
  }

  /**
   * Stop the worker pool. Waits for current jobs to finish.
   */
  async stop() {
    this.running = false;
    await Promise.all(this.workers.map(w => w.stop()));
  }

  /**
   * Submit a job to the queue. Throws if queue is full.
   */
  async submit(job: Job): Promise<void> {
    if (!this.running) {
      throw new Error('Worker pool is not running');
    }
    
    if (!this.queue.enqueue(job)) {
      throw new Error('Queue full');
    }
  }

  /**
   * Get the current queue size.
   */
  getQueueSize(): number {
    return this.queue.size;
  }

  /**
   * Check if the queue is full.
   */
  isQueueFull(): boolean {
    return this.queue.isFull;
  }

  private startWorkers() {
    for (let i = 0; i < this.numWorkers; i++) {
      const worker = new Worker(i, this.queue, () => this.running);
      this.workers.push(worker);
      worker.start();
    }
  }
}

/**
 * Individual worker that processes jobs from the queue.
 */
class Worker {
  private processing = false;

  constructor(
    private id: number,
    private queue: BoundedQueue<Job>,
    private isRunning: () => boolean
  ) {}

  async start() {
    while (this.isRunning()) {
      const job = this.queue.dequeue();
      if (!job) {
        await this.sleep(100);
        continue;
      }

      this.processing = true;
      try {
        await job.execute();
      } catch (error) {
        try {
          await job.handleError(error as Error);
        } catch (handleError) {
          console.error(`Worker ${this.id} failed to handle error:`, handleError);
        }
      } finally {
        this.processing = false;
      }
    }
  }

  async stop() {
    // Wait for current job to finish
    while (this.processing) {
      await this.sleep(10);
    }
  }

  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

