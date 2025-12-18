/**
 * Gateway Middleware
 * 
 * Enforces trace_id propagation, per-agent tool allowlists,
 * and per-request token/time budgets.
 */

import { MessageEnvelope, AgentMessage, AgentInfo, PolicyRule } from '../types';

export interface AgentRegistry {
  get(agentId: string): Promise<AgentInfo | null>;
  register(agent: AgentInfo): Promise<void>;
}

export interface PolicyEngine {
  getPolicy(agentId: string): Promise<PolicyRule | null>;
  checkAccess(agentId: string, resource: string): Promise<boolean>;
}

export interface BudgetTracker {
  getUsage(agentId: string): Promise<{ tokens_used: number; requests_count: number }>;
  recordUsage(agentId: string, tokens: number): Promise<void>;
}

export class GatewayMiddleware {
  constructor(
    private agentRegistry: AgentRegistry,
    private policyEngine: PolicyEngine,
    private budgetTracker: BudgetTracker
  ) {}

  async processRequest(envelope: MessageEnvelope): Promise<MessageEnvelope> {
    // 1. Validate trace_id propagation
    if (!envelope.trace_id) {
      envelope.trace_id = this.generateTraceId();
    }

    // 2. Check per-agent tool allowlist
    const agentInfo = await this.agentRegistry.get(envelope.auth.agent_id);
    if (!agentInfo) {
      throw new Error(`Agent ${envelope.auth.agent_id} not found in registry`);
    }

    const message = envelope.payload as AgentMessage;
    if (message.type === 'request' && message.action.startsWith('tool:')) {
      const toolName = message.action.replace('tool:', '');
      if (!agentInfo.allowed_tools.includes(toolName)) {
        throw new Error(
          `Tool ${toolName} not allowed for agent ${envelope.auth.agent_id}`
        );
      }
    }

    // 3. Check per-request token/time budget
    if (envelope.budget.max_tokens) {
      const usage = await this.budgetTracker.getUsage(envelope.auth.agent_id);
      if (usage.tokens_used >= envelope.budget.max_tokens) {
        throw new Error('Token budget exceeded');
      }
    }

    if (envelope.budget.max_time_ms) {
      const startTime = Date.now();
      envelope.budget.spent_time_ms = startTime - envelope.timestamp;
      if (envelope.budget.spent_time_ms > envelope.budget.max_time_ms) {
        throw new Error('Time budget exceeded');
      }
    }

    // 4. Check delegation depth
    if (envelope.delegation_depth > 5) {
      throw new Error('Maximum delegation depth exceeded');
    }

    // 5. Check policy access
    const hasAccess = await this.policyEngine.checkAccess(
      envelope.auth.agent_id,
      envelope.target_agent
    );
    if (!hasAccess) {
      throw new Error(
        `Agent ${envelope.auth.agent_id} does not have access to ${envelope.target_agent}`
      );
    }

    return envelope;
  }

  private generateTraceId(): string {
    return `trace-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }
}

