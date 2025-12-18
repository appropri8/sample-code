/**
 * Example: OpenTelemetry instrumentation wrapper around agent step execution
 * 
 * This demonstrates how to instrument agent steps with OpenTelemetry spans,
 * tracking latency, token usage, and errors.
 */

import { NodeSDK } from '@opentelemetry/sdk-node';
import { getNodeAutoInstrumentations } from '@opentelemetry/auto-instrumentations-node';
import { InstrumentedAgentExecutor } from '../tracing/instrumented-agent-executor';

// Initialize OpenTelemetry SDK
const sdk = new NodeSDK({
  instrumentations: [getNodeAutoInstrumentations()],
});

sdk.start();

async function main() {
  console.log('=== Tracing Example: Instrumented Agent Executor ===\n');

  const executor = new InstrumentedAgentExecutor();

  // Execute an agent step
  const result = await executor.executeStep({
    agentId: 'agent-a',
    taskId: 'task-123',
    traceId: 'trace-abc-123',
    input: { query: 'What is the weather?' },
    model: 'gpt-4',
    promptVersion: 'v2.1',
  });

  console.log('Agent step result:');
  console.log(JSON.stringify(result, null, 2));
  console.log('\n✅ Check your OpenTelemetry backend (Jaeger, Tempo, etc.) for the trace');
}

main().catch(console.error);
