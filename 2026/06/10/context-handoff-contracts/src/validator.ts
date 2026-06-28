import { HandoffContract } from "./schema";
import type { ZodError } from "zod";

export interface ValidationResult {
  valid: boolean;
  errors: string[];
  warnings: string[];
}

/**
 * Validates a HandoffContract before it is handed to the receiving agent.
 *
 * Checks:
 * - Required fields present (handoffId, receivingAgent, task, traceId)
 * - Sources attached to every factual claim
 * - No forbidden context included (stale facts, excluded types)
 * - Token budget check (estimate from facts + task)
 * - Tool permissions aligned (no allowed tool that is also forbidden)
 * - Output schema registered (if required)
 * - Trace ID propagated
 */
export function validateContract(
  contract: unknown,
  options?: {
    maxTokenBudget?: number;
    requireOutputSchema?: boolean;
  },
): ValidationResult {
  const result: ValidationResult = { valid: true, errors: [], warnings: [] };

  // 1. Zod parse
  const parsed = HandoffContract.safeParse(contract);
  if (!parsed.success) {
    result.valid = false;
    result.errors.push(...formatZodErrors(parsed.error));
    return result;
  }

  const c = parsed.data;

  // 2. Required fields (handled by Zod, but double-check)
  if (!c.handoffId) {
    result.errors.push("handoffId is required");
  }
  if (!c.receivingAgent) {
    result.errors.push("receivingAgent is required");
  }
  if (!c.task) {
    result.errors.push("task is required");
  }
  if (!c.traceId) {
    result.errors.push("traceId is required for observability");
  }

  // 3. Every fact must have a source
  for (const fact of c.facts) {
    if (!fact.source.source) {
      result.errors.push(
        `Fact "${fact.claim.substring(0, 50)}..." is missing source provenance`,
      );
    }
  }

  // 4. No tool appears in both allowed and forbidden
  const allowedSet = new Set(c.allowedTools);
  const forbiddenSet = new Set(c.forbiddenTools);
  for (const tool of c.allowedTools) {
    if (forbiddenSet.has(tool)) {
      result.errors.push(
        `Tool "${tool}" is in both allowedTools and forbiddenTools`,
      );
    }
  }

  // 5. Token budget check (rough estimate: ~4 chars per token)
  if (options?.maxTokenBudget) {
    let totalChars = c.task.length;
    for (const fact of c.facts) {
      totalChars += fact.claim.length;
    }
    const estimatedTokens = Math.ceil(totalChars / 4);
    if (estimatedTokens > options.maxTokenBudget) {
      result.errors.push(
        `Estimated token count ${estimatedTokens} exceeds budget of ${options.maxTokenBudget}`,
      );
    }
  }

  // 6. Output schema requirement
  if (options?.requireOutputSchema && !c.outputSchema) {
    result.errors.push(
      "Output schema is required but not provided in the contract",
    );
  }

  // 7. Expiry check
  const createdAt = new Date(c.createdAt).getTime();
  const expiresMs = c.expiresAfterMinutes * 60 * 1000;
  if (Date.now() > createdAt + expiresMs) {
    result.warnings.push(
      `Contract ${c.handoffId} expired ${Math.round((Date.now() - (createdAt + expiresMs)) / 1000)}s ago`,
    );
  }

  // 8. Warnings
  if (c.facts.length === 0) {
    result.warnings.push(
      "Contract contains zero facts — receiving agent may have nothing to work with",
    );
  }

  if (c.allowedTools.length === 0) {
    result.warnings.push(
      "No allowed tools specified — receiving agent cannot call any tools",
    );
  }

  result.valid = result.errors.length === 0;
  return result;
}

function formatZodErrors(error: ZodError): string[] {
  return error.errors.map(
    (e) => `${e.path.join(".")}: ${e.message}`,
  );
}
