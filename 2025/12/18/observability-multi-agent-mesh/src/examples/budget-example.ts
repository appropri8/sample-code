/**
 * Example: Budget manager with token/time/tool limits and stop conditions
 * 
 * This demonstrates how to enforce budgets and prevent runaway costs.
 */

import { BudgetManager } from '../budget/budget-manager';

async function main() {
  console.log('=== Budget Example: Token/Time/Tool Limits ===\n');

  const budgetManager = new BudgetManager();
  const taskId = 'task-123';

  // Create a budget
  budgetManager.createBudget(taskId, {
    maxTokens: 1000,
    maxTimeMs: 5000,
    maxToolCalls: 10,
    maxToolCallsPerClass: {
      'database': 5,
      'api': 3,
    },
  });

  console.log('✅ Budget created for task:', taskId);

  // Check token budget
  try {
    budgetManager.checkTokenBudget(taskId, 500);
    console.log('✅ Token budget check passed: 500 tokens');
    
    budgetManager.checkTokenBudget(taskId, 400);
    console.log('✅ Token budget check passed: 400 more tokens (total: 900)');
    
    budgetManager.checkTokenBudget(taskId, 200);
    console.log('❌ This should fail (would exceed 1000 token limit)');
  } catch (error) {
    console.log('✅ Token budget enforcement working:', (error as Error).message);
  }

  // Check tool call budget
  try {
    for (let i = 0; i < 5; i++) {
      budgetManager.checkToolCallBudget(taskId, 'database-query', 'database');
      console.log(`✅ Tool call ${i + 1}/5 for database class`);
    }
    
    budgetManager.checkToolCallBudget(taskId, 'database-query', 'database');
    console.log('❌ This should fail (exceeded database class limit)');
  } catch (error) {
    console.log('✅ Tool call budget enforcement working:', (error as Error).message);
  }

  // Check stop conditions
  try {
    budgetManager.checkStopConditions(taskId, 50, 2, 'task-signature-1');
    console.log('✅ Stop condition check passed');
    
    budgetManager.checkStopConditions(taskId, 101, 2, 'task-signature-2');
    console.log('❌ This should fail (exceeded max iterations)');
  } catch (error) {
    console.log('✅ Stop condition enforcement working:', (error as Error).message);
  }

  // Check circular task detection
  try {
    budgetManager.checkStopConditions(taskId, 10, 2, 'task-signature-3');
    budgetManager.checkStopConditions(taskId, 11, 2, 'task-signature-3');
    console.log('❌ This should fail (circular task detected)');
  } catch (error) {
    console.log('✅ Circular task detection working:', (error as Error).message);
  }

  // Get budget status
  const budget = budgetManager.getBudget(taskId);
  if (budget) {
    console.log('\n=== Budget Status ===');
    console.log(`Spent tokens: ${budget.spent_tokens}/${budget.max_tokens}`);
    console.log(`Spent tool calls: ${budget.spent_tool_calls}/${budget.max_tool_calls}`);
    console.log(`Elapsed time: ${budget.spent_time_ms}ms/${budget.max_time_ms}ms`);
  }

  console.log('\n✅ Budget management working correctly');
}

main().catch(console.error);
