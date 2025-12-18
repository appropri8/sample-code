import { trace, Span, SpanStatusCode } from '@opentelemetry/api';

interface AgentStep {
  agentId: string;
  taskId: string;
  traceId: string;
  parentSpanId?: string;
  input: unknown;
  model: string;
  promptVersion: string;
}

interface AgentStepResult {
  output: unknown;
  tokenUsage: { input: number; output: number };
  latencyMs: number;
  error?: Error;
}

/**
 * OpenTelemetry instrumentation wrapper around agent step execution.
 * Creates spans for every agent step, tracks latency, token usage, and errors.
 */
export class InstrumentedAgentExecutor {
  private tracer = trace.getTracer('agent-mesh');

  async executeStep(step: AgentStep): Promise<AgentStepResult> {
    const span = this.tracer.startSpan(`agent.${step.agentId}`, {
      attributes: {
        'agent.id': step.agentId,
        'task.id': step.taskId,
        'trace.id': step.traceId,
        'model': step.model,
        'prompt.version': step.promptVersion,
      },
    });

    const startTime = Date.now();
    let result: AgentStepResult;

    try {
      // Execute agent step (your actual agent logic)
      const output = await this.runAgentStep(step);
      
      const latencyMs = Date.now() - startTime;
      const tokenUsage = this.estimateTokenUsage(step.input, output);

      span.setAttributes({
        'agent.latency_ms': latencyMs,
        'agent.tokens.input': tokenUsage.input,
        'agent.tokens.output': tokenUsage.output,
        'agent.status': 'success',
      });

      result = {
        output,
        tokenUsage,
        latencyMs,
      };

      span.setStatus({ code: SpanStatusCode.OK });
    } catch (error) {
      const latencyMs = Date.now() - startTime;
      
      span.setAttributes({
        'agent.latency_ms': latencyMs,
        'agent.status': 'error',
        'error.message': (error as Error).message,
        'error.type': (error as Error).constructor.name,
      });

      span.setStatus({
        code: SpanStatusCode.ERROR,
        message: (error as Error).message,
      });

      result = {
        output: null,
        tokenUsage: { input: 0, output: 0 },
        latencyMs,
        error: error as Error,
      };
    } finally {
      span.end();
    }

    return result;
  }

  private async runAgentStep(step: AgentStep): Promise<unknown> {
    // Your actual agent execution logic
    // This is a placeholder that simulates agent work
    await new Promise(resolve => setTimeout(resolve, 100));
    return { 
      result: 'placeholder',
      agentId: step.agentId,
      taskId: step.taskId,
    };
  }

  private estimateTokenUsage(input: unknown, output: unknown): { input: number; output: number } {
    // Simple estimation (in production, use actual token counting)
    const inputStr = JSON.stringify(input);
    const outputStr = JSON.stringify(output);
    return {
      input: Math.ceil(inputStr.length / 4), // Rough estimate: 4 chars per token
      output: Math.ceil(outputStr.length / 4),
    };
  }
}
