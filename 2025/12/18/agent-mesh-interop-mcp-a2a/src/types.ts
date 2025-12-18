/**
 * Message Envelope Schema
 * 
 * All agents use this envelope format for communication.
 * It includes trace_id, tenant_id, auth, budget, and routing information.
 */

export interface MessageEnvelope {
  trace_id: string;
  tenant_id: string;
  auth: {
    agent_id: string;
    token: string;
    expires_at: number;
  };
  budget: {
    max_tokens?: number;
    max_time_ms?: number;
    spent_tokens?: number;
    spent_time_ms?: number;
  };
  source_agent: string;
  target_agent: string;
  payload: unknown;
  timestamp: number;
  delegation_depth: number;
}

export interface AgentMessage {
  type: 'request' | 'response' | 'error';
  task_id: string;
  action: string;
  parameters: Record<string, unknown>;
  context?: Record<string, unknown>;
}

export interface AgentInfo {
  agent_id: string;
  name: string;
  capabilities: string[];
  location: string;
  allowed_tools: string[];
  metadata?: Record<string, unknown>;
}

export interface ToolDefinition {
  name: string;
  description: string;
  inputSchema: {
    type: string;
    properties: Record<string, unknown>;
    required?: string[];
  };
  handler: (args: unknown) => Promise<unknown>;
}

export interface PolicyRule {
  agent_id: string;
  allowed_tools: string[];
  rate_limit?: {
    requests_per_second: number;
    requests_per_minute: number;
  };
  budget_limit?: {
    tokens_per_hour: number;
    tokens_per_day: number;
  };
}

