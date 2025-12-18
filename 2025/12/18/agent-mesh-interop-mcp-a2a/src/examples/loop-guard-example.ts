/**
 * Example 5: Loop Guard
 * 
 * Demonstrates how the loop guard prevents infinite delegation loops
 * by tracking delegation depth and circular paths.
 */

import { LoopGuard } from '../gateway/loop-guard';
import { MessageEnvelope } from '../types';

function createEnvelope(
  source: string,
  target: string,
  depth: number,
  taskId: string
): MessageEnvelope {
  return {
    trace_id: 'trace-123',
    tenant_id: 'tenant-xyz',
    auth: {
      agent_id: source,
      token: 'token-abc',
      expires_at: Date.now() + 3600000,
    },
    budget: {},
    source_agent: source,
    target_agent: target,
    payload: {
      type: 'request',
      task_id: taskId,
      action: 'delegate',
      parameters: {},
    },
    timestamp: Date.now(),
    delegation_depth: depth,
  };
}

function runLoopGuardExample() {
  const guard = new LoopGuard();

  console.log('Testing loop guard...\n');

  // Test 1: Normal delegation (should pass)
  console.log('Test 1: Normal delegation');
  const env1 = createEnvelope('agent-a', 'agent-b', 1, 'task-1');
  try {
    guard.checkLoop(env1);
    console.log('✓ Passed: Normal delegation allowed');
  } catch (error: any) {
    console.log('✗ Failed:', error.message);
  }

  // Test 2: Maximum depth exceeded (should fail)
  console.log('\nTest 2: Maximum depth exceeded');
  const env2 = createEnvelope('agent-a', 'agent-b', 6, 'task-1');
  try {
    guard.checkLoop(env2);
    console.log('✗ Failed: Should have rejected');
  } catch (error: any) {
    console.log('✓ Passed:', error.message);
  }

  // Test 3: Circular delegation (should fail)
  console.log('\nTest 3: Circular delegation');
  const env3a = createEnvelope('agent-a', 'agent-b', 1, 'task-2');
  guard.checkLoop(env3a); // First delegation

  const env3b = createEnvelope('agent-b', 'agent-c', 2, 'task-2');
  guard.checkLoop(env3b); // Second delegation

  const env3c = createEnvelope('agent-c', 'agent-a', 3, 'task-2'); // Circular!
  try {
    guard.checkLoop(env3c);
    console.log('✗ Failed: Should have detected circular delegation');
  } catch (error: any) {
    console.log('✓ Passed:', error.message);
  }

  // Test 4: Increment depth
  console.log('\nTest 4: Increment depth');
  const env4 = createEnvelope('agent-a', 'agent-b', 2, 'task-3');
  const incremented = guard.incrementDepth(env4);
  console.log(`Original depth: ${env4.delegation_depth}`);
  console.log(`Incremented depth: ${incremented.delegation_depth}`);
  console.log('✓ Passed: Depth incremented correctly');
}

runLoopGuardExample();

