import {
  HandoffContract,
  SessionEvent,
  Fact,
  SourceProvenance,
  type ConfidenceLevel,
} from "./schema";

export interface CompilerOptions {
  /** Context categories to exclude (matched against event types) */
  excludedEventTypes?: SessionEvent["type"][];
  /** Maximum age in minutes for a tool_result event to be considered fresh */
  maxResultAgeMinutes?: number;
  /** Default expiry for the contract */
  defaultExpiryMinutes?: number;
  /** Trace ID for observability */
  traceId?: string;
}

const DEFAULT_OPTIONS: Required<CompilerOptions> = {
  excludedEventTypes: ["brainstorm", "internal_note"],
  maxResultAgeMinutes: 30,
  defaultExpiryMinutes: 30,
  traceId: "manual",
};

/**
 * Converts a raw array of session events into a minimal HandoffContract.
 *
 * - Filters out events marked as `excludeFromHandoff`
 * - Filters out events matching excludedEventTypes
 * - Rejects stale tool results (> maxResultAgeMinutes old)
 * - Extracts factual claims from tool results and LLM responses
 * - Sets provenance on every fact
 */
export function compileHandoffContract(
  handoffId: string,
  receivingAgent: string,
  task: string,
  events: SessionEvent[],
  options: CompilerOptions = {},
): HandoffContract {
  const opts = { ...DEFAULT_OPTIONS, ...options };
  const now = new Date().toISOString();

  // Step 1: Filter events
  const filtered = events.filter((evt) => {
    // Explicitly excluded
    if (evt.excludeFromHandoff) return false;

    // Excluded by type
    if (opts.excludedEventTypes.includes(evt.type)) return false;

    // Stale tool results
    if (evt.type === "tool_result" && evt.maxAgeMinutes) {
      const eventTime = new Date(evt.timestamp).getTime();
      const ageMinutes = (Date.now() - eventTime) / 60_000;
      if (ageMinutes > evt.maxAgeMinutes) return false;
    }

    return true;
  });

  // Step 2: Extract facts from filtered events
  const facts: Fact[] = [];
  const excludedContextLabels: string[] = [];

  for (const evt of filtered) {
    if (evt.type === "tool_result" && evt.success !== false) {
      const provenance: SourceProvenance = {
        source: evt.toolName ?? "unknown_tool",
        timestamp: evt.timestamp,
        method: `tool_call:${evt.toolName}`,
      };

      facts.push({
        claim: evt.content,
        source: provenance,
        confidence: "high",
        eventId: evt.id,
      });
    }

    if (evt.type === "llm_response") {
      const provenance: SourceProvenance = {
        source: "llm",
        timestamp: evt.timestamp,
        method: "llm_generation",
      };

      facts.push({
        claim: evt.content,
        source: provenance,
        confidence: "medium",
        eventId: evt.id,
      });
    }

    if (evt.type === "user_message") {
      const provenance: SourceProvenance = {
        source: "user",
        timestamp: evt.timestamp,
        method: "user_input",
      };

      facts.push({
        claim: evt.content,
        source: provenance,
        confidence: "unverified",
        eventId: evt.id,
      });
    }
  }

  // Step 3: Build excluded context labels from what we filtered out
  for (const evt of events) {
    if (evt.excludeFromHandoff) {
      excludedContextLabels.push(`explicit:${evt.type}`);
    } else if (opts.excludedEventTypes.includes(evt.type)) {
      excludedContextLabels.push(`type:${evt.type}`);
    } else if (
      evt.type === "tool_result" &&
      evt.maxAgeMinutes &&
      (Date.now() - new Date(evt.timestamp).getTime()) / 60_000 >
        evt.maxAgeMinutes
    ) {
      excludedContextLabels.push(`stale:${evt.toolName ?? evt.type}`);
    }
  }

  // Step 4: Determine allowed tools from tool_result events that were included
  const allowedTools = [
    ...new Set(
      filtered
        .filter((evt) => evt.toolName)
        .map((evt) => evt.toolName!),
    ),
  ];

  // Build the contract
  return HandoffContract.parse({
    handoffId,
    receivingAgent,
    task,
    facts,
    excludedContext: [...new Set(excludedContextLabels)],
    allowedTools,
    forbiddenTools: [], // set by policy, not derived from events
    outputSchema: undefined,
    expiresAfterMinutes: opts.defaultExpiryMinutes,
    createdAt: now,
    traceId: opts.traceId,
  });
}
