/**
 * Example 2: Gateway Middleware Usage
 * 
 * Demonstrates how the gateway enforces policies,
 * validates budgets, and checks tool allowlists.
 */

import { GatewayMiddleware, AgentRegistry, PolicyEngine, BudgetTracker } from '../gateway/middleware';
import { MessageEnvelope, AgentInfo, PolicyRule } from '../types';

// Simple in-memory implementations for demo
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
  private policies: Map<string, PolicyRule> = new Map();

  async getPolicy(agentId: string): Promise<PolicyRule | null> {
    return this.policies.get(agentId) || null;
  }

  async checkAccess(agentId: string, resource: string): Promise<boolean> {
    const policy = await this.getPolicy(agentId);
    if (!policy) return false;
    // Simple access check - in reality this would be more complex
    return true;
  }

  setPolicy(agentId: string, policy: PolicyRule): void {
    this.policies.set(agentId, policy);
  }
}

class InMemoryBudgetTracker implements BudgetTracker {
  private usage: Map<string, { tokens_used: number; requests_count: number }> = new Map();

  async getUsage(agentId: string): Promise<{ tokens_used: number; requests_count: number }> {
    return this.usage.get(agentId) || { tokens_used: 0, requests_count: 0 };
  }

  async recordUsage(agentId: string, tokens: number): Promise<void> {
    const current = await this.getUsage(agentId);
    this.usage.set(agentId, {
      tokens_used: current.tokens_used + tokens,
      requests_count: current.requests_count + 1,
    });
  }
}

async function runGatewayExample() {
  // Setup
  const registry = new InMemoryAgentRegistry();
  const policyEngine = new InMemoryPolicyEngine();
  const budgetTracker = new InMemoryBudgetTracker();
  const gateway = new GatewayMiddleware(registry, policyEngine, budgetTracker);

  // Register an agent
  await registry.register({
    agent_id: 'agent-a',
    name: 'Agent A',
    capabilities: ['process_orders', 'calculate_totals'],
    location: 'http://localhost:8001',
    allowed_tools: ['calculator', 'database'],
  });

  // Set policy
  policyEngine.setPolicy('agent-a', {
    agent_id: 'agent-a',
    allowed_tools: ['calculator', 'database'],
    rate_limit: {
      requests_per_second: 10,
      requests_per_minute: 100,
    },
    budget_limit: {
      tokens_per_hour: 10000,
      tokens_per_day: 100000,
    },
  });

  // Create a message envelope
  const envelope: MessageEnvelope = {
    trace_id: 'trace-123',
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
      action: 'tool:calculator',
      parameters: { operation: 'add', a: 1, b: 2 },
    },
    timestamp: Date.now(),
    delegation_depth: 0,
  };

  try {
    // Process through gateway
    const processed = await gateway.processRequest(envelope);
    console.log('Gateway processed successfully:', processed.trace_id);
  } catch (error: any) {
    console.error('Gateway rejected request:', error.message);
  }

  // Try with disallowed tool
  const badEnvelope: MessageEnvelope = {
    ...envelope,
    payload: {
      type: 'request',
      task_id: 'task-124',
      action: 'tool:unauthorized_tool',
      parameters: {},
    },
  };

  try {
    await gateway.processRequest(badEnvelope);
    console.log('This should not happen');
  } catch (error: any) {
    console.log('Gateway correctly rejected unauthorized tool:', error.message);
  }
}

runGatewayExample().catch(console.error);

