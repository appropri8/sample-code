/**
 * Example 4: A2A Message Handler
 * 
 * Demonstrates how agents communicate using A2A protocol
 * through the message handler and gateway.
 */

import { A2AMessageHandler } from '../a2a/message-handler';
import { GatewayMiddleware, AgentRegistry, PolicyEngine, BudgetTracker } from '../gateway/middleware';
import { MessageEnvelope, AgentInfo } from '../types';

// Reuse in-memory implementations from gateway example
class InMemoryAgentRegistry implements AgentRegistry {
  private agents: Map<string, AgentInfo> = new Map();

  async get(agentId: string): Promise<AgentInfo | null> {
    return this.agents.get(agentId) || null;
  }

  async register(agent: AgentInfo): Promise<void> {
    this.agents.set(agent.agent_id, agent);
  }
}

class InMemoryPolicyEngine implements PolicyEngine {
  async getPolicy(agentId: string): Promise<any> {
    return null;
  }

  async checkAccess(agentId: string, resource: string): Promise<boolean> {
    return true;
  }
}

class InMemoryBudgetTracker implements BudgetTracker {
  async getUsage(agentId: string): Promise<{ tokens_used: number; requests_count: number }> {
    return { tokens_used: 0, requests_count: 0 };
  }

  async recordUsage(agentId: string, tokens: number): Promise<void> {
    // No-op for demo
  }
}

async function runA2AExample() {
  // Setup
  const registry = new InMemoryAgentRegistry();
  const policyEngine = new InMemoryPolicyEngine();
  const budgetTracker = new InMemoryBudgetTracker();
  const gateway = new GatewayMiddleware(registry, policyEngine, budgetTracker);
  const handler = new A2AMessageHandler(registry, gateway);

  // Register agents
  await registry.register({
    agent_id: 'agent-a',
    name: 'Agent A',
    capabilities: ['process_orders'],
    location: 'http://localhost:8001',
    allowed_tools: ['calculator'],
  });

  await registry.register({
    agent_id: 'agent-b',
    name: 'Agent B',
    capabilities: ['validate_orders'],
    location: 'http://localhost:8002',
    allowed_tools: ['database'],
  });

  // Create message from Agent A to Agent B
  const envelope: MessageEnvelope = {
    trace_id: 'trace-abc-123',
    tenant_id: 'tenant-xyz',
    auth: {
      agent_id: 'agent-a',
      token: 'token-abc',
      expires_at: Date.now() + 3600000,
    },
    budget: {
      max_tokens: 1000,
      max_time_ms: 5000,
    },
    source_agent: 'agent-a',
    target_agent: 'agent-b',
    payload: {
      type: 'request',
      task_id: 'task-123',
      action: 'validate_order',
      parameters: {
        order_id: 'order-456',
        items: ['item1', 'item2'],
      },
    },
    timestamp: Date.now(),
    delegation_depth: 0,
  };

  console.log('Sending message from Agent A to Agent B...');
  console.log('Envelope:', JSON.stringify(envelope, null, 2));

  try {
    // Handle message through A2A handler
    const response = await handler.handleMessage(envelope);
    console.log('\nResponse received:');
    console.log(JSON.stringify(response, null, 2));
  } catch (error: any) {
    console.error('Error handling message:', error.message);
  }
}

runA2AExample().catch(console.error);

