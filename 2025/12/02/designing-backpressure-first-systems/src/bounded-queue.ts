/**
 * Bounded Queue
 * 
 * A queue with a maximum size. When full, enqueue operations fail.
 */

export class BoundedQueue<T> {
  private queue: T[] = [];

  constructor(private maxSize: number) {
    if (maxSize <= 0) {
      throw new Error('Max size must be greater than 0');
    }
  }

  /**
   * Add an item to the queue. Returns true if successful, false if queue is full.
   */
  enqueue(item: T): boolean {
    if (this.queue.length >= this.maxSize) {
      return false;
    }
    this.queue.push(item);
    return true;
  }

  /**
   * Remove and return the first item from the queue.
   */
  dequeue(): T | undefined {
    return this.queue.shift();
  }

  /**
   * Get the current size of the queue.
   */
  get size(): number {
    return this.queue.length;
  }

  /**
   * Check if the queue is full.
   */
  get isFull(): boolean {
    return this.queue.length >= this.maxSize;
  }

  /**
   * Check if the queue is empty.
   */
  get isEmpty(): boolean {
    return this.queue.length === 0;
  }

  /**
   * Clear the queue.
   */
  clear(): void {
    this.queue = [];
  }
}

/**
 * Priority Queue
 * 
 * A queue that processes items by priority. Higher priority items are processed first.
 */
export class PriorityQueue<T> {
  private queues: Map<number, T[]> = new Map();

  /**
   * Add an item with a priority. Higher numbers = higher priority.
   */
  enqueue(item: T, priority: number) {
    if (!this.queues.has(priority)) {
      this.queues.set(priority, []);
    }
    this.queues.get(priority)!.push(item);
  }

  /**
   * Remove and return the highest priority item.
   */
  dequeue(): T | undefined {
    const priorities = Array.from(this.queues.keys()).sort((a, b) => b - a);
    for (const priority of priorities) {
      const queue = this.queues.get(priority);
      if (queue && queue.length > 0) {
        return queue.shift();
      }
    }
    return undefined;
  }

  /**
   * Drop all low-priority items. Returns the number of items dropped.
   */
  dropLowPriority(): number {
    if (this.queues.size === 0) return 0;
    
    const lowPriority = Math.min(...Array.from(this.queues.keys()));
    const queue = this.queues.get(lowPriority);
    if (queue) {
      const dropped = queue.length;
      queue.length = 0;
      return dropped;
    }
    return 0;
  }

  /**
   * Get the total number of items in all priority queues.
   */
  get size(): number {
    let total = 0;
    for (const queue of this.queues.values()) {
      total += queue.length;
    }
    return total;
  }

  /**
   * Check if the queue is empty.
   */
  get isEmpty(): boolean {
    return this.size === 0;
  }
}

