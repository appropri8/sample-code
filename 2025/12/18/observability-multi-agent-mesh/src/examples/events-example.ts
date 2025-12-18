/**
 * Example: AgentEvent schema and logger (structured JSON)
 * 
 * This demonstrates how to emit structured events for all agent operations,
 * enabling correlation through trace_id, span_id, and task_id.
 */

import { AgentEventLogger, InMemoryEventStore } from '../events/agent-event-logger';

async function main() {
  console.log('=== Events Example: Structured Event Logging ===\n');

  const eventStore = new InMemoryEventStore();
  const logger = new AgentEventLogger(eventStore);

  const traceId = 'trace-123';
  const taskId = 'task-456';
  const agentId = 'agent-a';

  // Log agent started
  logger.logAgentStarted(
    traceId,
    'span-1',
    taskId,
    agentId,
    {
      model: 'gpt-4',
      prompt_version: 'v2.1',
      tenant_id: 'tenant-abc',
    }
  );

  // Log tool called
  logger.logToolCalled(
    traceId,
    'span-2',
    'span-1',
    taskId,
    agentId,
    'database_query',
    { query: 'SELECT * FROM users' }
  );

  // Log tool result
  logger.logToolResult(
    traceId,
    'span-2',
    taskId,
    agentId,
    'database_query',
    { rows: [{ id: 1, name: 'Alice' }] },
    45,
    true
  );

  // Log agent delegation
  logger.logAgentDelegated(
    traceId,
    'span-1',
    taskId,
    'agent-a',
    'agent-b',
    { task: 'process_order' }
  );

  // Log agent completed
  logger.logAgentCompleted(
    traceId,
    'span-1',
    taskId,
    agentId,
    { status: 'success', data: { result: 'processed' } },
    150,
    { input: 500, output: 200 }
  );

  console.log('\n=== Querying events by trace_id ===');
  const traceEvents = await eventStore.queryByTraceId(traceId);
  console.log(`Found ${traceEvents.length} events for trace ${traceId}\n`);

  console.log('\n=== Querying events by task_id ===');
  const taskEvents = await eventStore.queryByTaskId(taskId);
  console.log(`Found ${taskEvents.length} events for task ${taskId}\n`);

  console.log('\n=== Querying events by agent_id ===');
  const agentEvents = await eventStore.queryByAgentId(agentId);
  console.log(`Found ${agentEvents.length} events for agent ${agentId}\n`);

  console.log('✅ All events logged and queryable');
}

main().catch(console.error);
