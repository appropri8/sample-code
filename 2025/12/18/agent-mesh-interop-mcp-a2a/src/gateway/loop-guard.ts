/**
 * Loop Guard
 * 
 * Prevents infinite delegation loops by tracking:
 * - Maximum delegation depth
 * - Seen-task hash set
 */

import { MessageEnvelope } from '../types';

export class LoopGuard {
  private seenTasks: Map<string, Set<string>> = new Map();
  private readonly MAX_DEPTH = 5;
  private readonly TTL_MS = 60000; // 1 minute

  checkLoop(envelope: MessageEnvelope): void {
    // Check delegation depth
    if (envelope.delegation_depth > this.MAX_DEPTH) {
      throw new Error(
        `Maximum delegation depth ${this.MAX_DEPTH} exceeded. Current depth: ${envelope.delegation_depth}`
      );
    }

    // Check for circular delegation
    const taskKey = this.getTaskKey(envelope);
    const seenSet = this.seenTasks.get(taskKey) || new Set();
    
    const delegationPath = `${envelope.source_agent}->${envelope.target_agent}`;
    if (seenSet.has(delegationPath)) {
      throw new Error(
        `Circular delegation detected: ${delegationPath} for task ${taskKey}`
      );
    }

    // Track this delegation
    seenSet.add(delegationPath);
    this.seenTasks.set(taskKey, seenSet);

    // Cleanup old entries after TTL
    setTimeout(() => {
      this.seenTasks.delete(taskKey);
    }, this.TTL_MS);
  }

  private getTaskKey(envelope: MessageEnvelope): string {
    const message = envelope.payload as { task_id?: string };
    return `${envelope.trace_id}:${message.task_id || 'unknown'}`;
  }

  incrementDepth(envelope: MessageEnvelope): MessageEnvelope {
    return {
      ...envelope,
      delegation_depth: (envelope.delegation_depth || 0) + 1,
    };
  }

  reset(): void {
    this.seenTasks.clear();
  }
}

