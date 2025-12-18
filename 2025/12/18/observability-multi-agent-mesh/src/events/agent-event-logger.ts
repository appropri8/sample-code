/**
 * Shared AgentEvent schema and logger for structured event logging.
 * All events follow a consistent structure with trace_id, span_id, task_id for correlation.
 */

export type AgentEventType = 
  | 'AgentStarted'
  | 'ToolCalled'
  | 'ToolResult'
  | 'AgentDelegated'
  | 'AgentCompleted'
  | 'AgentError';

export interface BaseAgentEvent {
  event: AgentEventType;
  trace_id: string;
  span_id: string;
  task_id: string;
  timestamp: number;
  agent_id: string;
  metadata: Record<string, unknown>;
}

export interface AgentStartedEvent extends BaseAgentEvent {
  event: 'AgentStarted';
  metadata: {
    model: string;
    prompt_version: string;
    tenant_id: string;
  };
}

export interface ToolCalledEvent extends BaseAgentEvent {
  event: 'ToolCalled';
  parent_span_id: string;
  tool_name: string;
  tool_input: unknown;
}

export interface ToolResultEvent extends BaseAgentEvent {
  event: 'ToolResult';
  tool_name: string;
  tool_output: unknown;
  latency_ms: number;
  success: boolean;
}

export interface AgentDelegatedEvent extends BaseAgentEvent {
  event: 'AgentDelegated';
  source_agent: string;
  target_agent: string;
  delegation_context: Record<string, unknown>;
}

export interface AgentCompletedEvent extends BaseAgentEvent {
  event: 'AgentCompleted';
  result: unknown;
  latency_ms: number;
  token_usage: { input: number; output: number };
}

export type AgentEvent = 
  | AgentStartedEvent
  | ToolCalledEvent
  | ToolResultEvent
  | AgentDelegatedEvent
  | AgentCompletedEvent;

/**
 * Simple in-memory event store for demonstration.
 * In production, use Elasticsearch, ClickHouse, or similar.
 */
export class InMemoryEventStore {
  private events: AgentEvent[] = [];

  async ingest(event: AgentEvent): Promise<void> {
    this.events.push(event);
    // In production, this would write to a persistent store
    console.log(JSON.stringify(event, null, 2));
  }

  async queryByTraceId(traceId: string): Promise<AgentEvent[]> {
    return this.events.filter(e => e.trace_id === traceId);
  }

  async queryByTaskId(taskId: string): Promise<AgentEvent[]> {
    return this.events.filter(e => e.task_id === taskId);
  }

  async queryByAgentId(agentId: string, startTime?: number, endTime?: number): Promise<AgentEvent[]> {
    return this.events.filter(e => {
      if (e.agent_id !== agentId) return false;
      if (startTime && e.timestamp < startTime) return false;
      if (endTime && e.timestamp > endTime) return false;
      return true;
    });
  }

  getAllEvents(): AgentEvent[] {
    return [...this.events];
  }
}

/**
 * AgentEventLogger emits structured events for all agent operations.
 * Every event includes trace_id, span_id, task_id for correlation.
 */
export class AgentEventLogger {
  constructor(private eventStore: InMemoryEventStore) {}

  logAgentStarted(
    traceId: string,
    spanId: string,
    taskId: string,
    agentId: string,
    metadata: { model: string; prompt_version: string; tenant_id: string }
  ): void {
    const event: AgentStartedEvent = {
      event: 'AgentStarted',
      trace_id: traceId,
      span_id: spanId,
      task_id: taskId,
      timestamp: Date.now(),
      agent_id: agentId,
      metadata,
    };
    this.eventStore.ingest(event);
  }

  logToolCalled(
    traceId: string,
    spanId: string,
    parentSpanId: string,
    taskId: string,
    agentId: string,
    toolName: string,
    toolInput: unknown
  ): void {
    const event: ToolCalledEvent = {
      event: 'ToolCalled',
      trace_id: traceId,
      span_id: spanId,
      parent_span_id: parentSpanId,
      task_id: taskId,
      timestamp: Date.now(),
      agent_id: agentId,
      tool_name: toolName,
      tool_input: toolInput,
      metadata: {},
    };
    this.eventStore.ingest(event);
  }

  logToolResult(
    traceId: string,
    spanId: string,
    taskId: string,
    agentId: string,
    toolName: string,
    toolOutput: unknown,
    latencyMs: number,
    success: boolean
  ): void {
    const event: ToolResultEvent = {
      event: 'ToolResult',
      trace_id: traceId,
      span_id: spanId,
      task_id: taskId,
      timestamp: Date.now(),
      agent_id: agentId,
      tool_name: toolName,
      tool_output: toolOutput,
      latency_ms: latencyMs,
      success,
      metadata: {},
    };
    this.eventStore.ingest(event);
  }

  logAgentDelegated(
    traceId: string,
    spanId: string,
    taskId: string,
    sourceAgent: string,
    targetAgent: string,
    delegationContext: Record<string, unknown>
  ): void {
    const event: AgentDelegatedEvent = {
      event: 'AgentDelegated',
      trace_id: traceId,
      span_id: spanId,
      task_id: taskId,
      timestamp: Date.now(),
      agent_id: sourceAgent,
      source_agent: sourceAgent,
      target_agent: targetAgent,
      delegation_context: delegationContext,
      metadata: {},
    };
    this.eventStore.ingest(event);
  }

  logAgentCompleted(
    traceId: string,
    spanId: string,
    taskId: string,
    agentId: string,
    result: unknown,
    latencyMs: number,
    tokenUsage: { input: number; output: number }
  ): void {
    const event: AgentCompletedEvent = {
      event: 'AgentCompleted',
      trace_id: traceId,
      span_id: spanId,
      task_id: taskId,
      timestamp: Date.now(),
      agent_id: agentId,
      result,
      latency_ms: latencyMs,
      token_usage: tokenUsage,
      metadata: {},
    };
    this.eventStore.ingest(event);
  }
}
