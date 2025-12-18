/**
 * Budget manager with token/time/tool limits and enforced stop conditions.
 * Prevents runaway costs by throwing errors when limits are exceeded.
 */

export interface TaskBudget {
  task_id: string;
  max_tokens: number;
  spent_tokens: number;
  max_time_ms: number;
  spent_time_ms: number;
  start_time: number;
  max_tool_calls: number;
  spent_tool_calls: number;
  max_tool_calls_per_class: Record<string, number>;
  spent_tool_calls_per_class: Record<string, number>;
}

export interface StopConditions {
  max_iterations: number;
  max_delegation_depth: number;
  seen_tasks: Set<string>;
}

export class BudgetManager {
  private budgets: Map<string, TaskBudget> = new Map();
  private stopConditions: Map<string, StopConditions> = new Map();

  createBudget(
    taskId: string,
    limits: {
      maxTokens?: number;
      maxTimeMs?: number;
      maxToolCalls?: number;
      maxToolCallsPerClass?: Record<string, number>;
    }
  ): void {
    const budget: TaskBudget = {
      task_id: taskId,
      max_tokens: limits.maxTokens ?? Infinity,
      spent_tokens: 0,
      max_time_ms: limits.maxTimeMs ?? Infinity,
      spent_time_ms: 0,
      start_time: Date.now(),
      max_tool_calls: limits.maxToolCalls ?? Infinity,
      spent_tool_calls: 0,
      max_tool_calls_per_class: limits.maxToolCallsPerClass ?? {},
      spent_tool_calls_per_class: {},
    };
    this.budgets.set(taskId, budget);

    const stopConditions: StopConditions = {
      max_iterations: 100,
      max_delegation_depth: 5,
      seen_tasks: new Set(),
    };
    this.stopConditions.set(taskId, stopConditions);
  }

  checkTokenBudget(taskId: string, tokensToSpend: number): void {
    const budget = this.budgets.get(taskId);
    if (!budget) {
      throw new Error(`No budget found for task ${taskId}`);
    }

    if (budget.spent_tokens + tokensToSpend > budget.max_tokens) {
      throw new Error(
        `Token budget exceeded for task ${taskId}: ${budget.spent_tokens + tokensToSpend} > ${budget.max_tokens}`
      );
    }

    budget.spent_tokens += tokensToSpend;
  }

  checkTimeBudget(taskId: string): void {
    const budget = this.budgets.get(taskId);
    if (!budget) {
      throw new Error(`No budget found for task ${taskId}`);
    }

    const elapsed = Date.now() - budget.start_time;
    budget.spent_time_ms = elapsed;

    if (elapsed > budget.max_time_ms) {
      throw new Error(
        `Time budget exceeded for task ${taskId}: ${elapsed}ms > ${budget.max_time_ms}ms`
      );
    }
  }

  checkToolCallBudget(taskId: string, toolName: string, toolClass?: string): void {
    const budget = this.budgets.get(taskId);
    if (!budget) {
      throw new Error(`No budget found for task ${taskId}`);
    }

    // Check total tool calls
    if (budget.spent_tool_calls >= budget.max_tool_calls) {
      throw new Error(
        `Tool call budget exceeded for task ${taskId}: ${budget.spent_tool_calls} >= ${budget.max_tool_calls}`
      );
    }

    // Check per-class tool calls
    if (toolClass && budget.max_tool_calls_per_class[toolClass]) {
      const spent = budget.spent_tool_calls_per_class[toolClass] || 0;
      const max = budget.max_tool_calls_per_class[toolClass];
      if (spent >= max) {
        throw new Error(
          `Tool call budget exceeded for class ${toolClass} in task ${taskId}: ${spent} >= ${max}`
        );
      }
      budget.spent_tool_calls_per_class[toolClass] = spent + 1;
    }

    budget.spent_tool_calls += 1;
  }

  checkStopConditions(
    taskId: string,
    iteration: number,
    delegationDepth: number,
    taskSignature: string
  ): void {
    const conditions = this.stopConditions.get(taskId);
    if (!conditions) {
      return; // No stop conditions set
    }

    // Check max iterations
    if (iteration > conditions.max_iterations) {
      throw new Error(
        `Max iterations exceeded for task ${taskId}: ${iteration} > ${conditions.max_iterations}`
      );
    }

    // Check max delegation depth
    if (delegationDepth > conditions.max_delegation_depth) {
      throw new Error(
        `Max delegation depth exceeded for task ${taskId}: ${delegationDepth} > ${conditions.max_delegation_depth}`
      );
    }

    // Check seen tasks
    if (conditions.seen_tasks.has(taskSignature)) {
      throw new Error(
        `Circular task detected for task ${taskId}: ${taskSignature}`
      );
    }

    conditions.seen_tasks.add(taskSignature);
  }

  getBudget(taskId: string): TaskBudget | undefined {
    return this.budgets.get(taskId);
  }

  cleanup(taskId: string): void {
    this.budgets.delete(taskId);
    this.stopConditions.delete(taskId);
  }
}
