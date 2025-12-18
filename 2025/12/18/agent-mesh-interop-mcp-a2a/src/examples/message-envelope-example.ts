/**
 * Example 1: Message Envelope Usage
 * 
 * Demonstrates how to create and use message envelopes
 * for agent-to-agent communication.
 */

import { MessageEnvelope, AgentMessage } from '../types';

function createMessageEnvelope(
  sourceAgent: string,
  targetAgent: string,
  message: AgentMessage,
  options: {
    traceId?: string;
    tenantId?: string;
    maxTokens?: number;
    maxTimeMs?: number;
  } = {}
): MessageEnvelope {
  return {
    trace_id: options.traceId || `trace-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    tenant_id: options.tenantId || 'default-tenant',
    auth: {
      agent_id: sourceAgent,
      token: `token-${sourceAgent}-${Date.now()}`,
      expires_at: Date.now() + 3600000, // 1 hour
    },
    budget: {
      max_tokens: options.maxTokens,
      max_time_ms: options.maxTimeMs,
      spent_tokens: 0,
      spent_time_ms: 0,
    },
    source_agent: sourceAgent,
    target_agent: targetAgent,
    payload: message,
    timestamp: Date.now(),
    delegation_depth: 0,
  };
}

// Example usage
const message: AgentMessage = {
  type: 'request',
  task_id: 'task-123',
  action: 'process_order',
  parameters: {
    order_id: 'order-456',
    items: ['item1', 'item2'],
  },
  context: {
    user_id: 'user-789',
  },
};

const envelope = createMessageEnvelope(
  'agent-a',
  'agent-b',
  message,
  {
    traceId: 'trace-abc-123',
    tenantId: 'tenant-xyz',
    maxTokens: 1000,
    maxTimeMs: 5000,
  }
);

console.log('Message Envelope:', JSON.stringify(envelope, null, 2));

