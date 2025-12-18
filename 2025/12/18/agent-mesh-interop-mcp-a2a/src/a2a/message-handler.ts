/**
 * A2A Message Handler
 * 
 * Routes and dispatches messages between agents using the A2A protocol.
 */

import { MessageEnvelope, AgentMessage, AgentInfo } from '../types';
import { GatewayMiddleware, AgentRegistry } from '../gateway/middleware';

export class A2AMessageHandler {
  constructor(
    private agentRegistry: AgentRegistry,
    private gateway: GatewayMiddleware
  ) {}

  async handleMessage(envelope: MessageEnvelope): Promise<MessageEnvelope> {
    // Process through gateway (policy checks, budget validation, etc.)
    const processed = await this.gateway.processRequest(envelope);

    // Route to target agent
    const targetAgent = await this.agentRegistry.get(processed.target_agent);
    if (!targetAgent) {
      throw new Error(`Target agent ${processed.target_agent} not found`);
    }

    // Dispatch to agent
    const message = processed.payload as AgentMessage;
    const response = await this.dispatchToAgent(targetAgent, message, processed);

    // Create response envelope
    return {
      ...processed,
      source_agent: processed.target_agent,
      target_agent: processed.source_agent,
      payload: response,
      timestamp: Date.now(),
    };
  }

  private async dispatchToAgent(
    agent: AgentInfo,
    message: AgentMessage,
    envelope: MessageEnvelope
  ): Promise<AgentMessage> {
    // In a real implementation, this would call the agent's handler
    // via HTTP, gRPC, or another transport mechanism
    const handler = this.getAgentHandler(agent);
    return await handler(message, envelope);
  }

  private getAgentHandler(
    agent: AgentInfo
  ): (msg: AgentMessage, env: MessageEnvelope) => Promise<AgentMessage> {
    // This would typically load the agent's handler from its implementation
    // For demo purposes, we return a simple handler
    return async (msg, env) => {
      // Simulate agent processing
      await this.simulateProcessing();

      // Return response
      return {
        type: 'response',
        task_id: msg.task_id,
        action: msg.action,
        parameters: {
          result: 'success',
          processed_by: agent.agent_id,
          trace_id: env.trace_id,
        },
        context: {
          ...msg.context,
          delegation_depth: env.delegation_depth,
        },
      };
    };
  }

  private async simulateProcessing(): Promise<void> {
    // Simulate some processing time
    await new Promise((resolve) => setTimeout(resolve, 100));
  }
}

