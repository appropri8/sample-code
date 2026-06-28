import { z } from "zod";

// ─── Confidence Level ───────────────────────────────────────────
export const ConfidenceLevel = z.enum(["high", "medium", "low", "unverified"]);
export type ConfidenceLevel = z.infer<typeof ConfidenceLevel>;

// ─── Source Provenance ───────────────────────────────────────────
export const SourceProvenance = z.object({
  /** Which system or function produced this fact (e.g. "crm.lookup_customer") */
  source: z.string().min(1),
  /** ISO-8601 timestamp of when this fact was retrieved */
  timestamp: z.string().datetime(),
  /** Human-readable description of how the fact was obtained */
  method: z.string().optional(),
});
export type SourceProvenance = z.infer<typeof SourceProvenance>;

// ─── Fact ────────────────────────────────────────────────────────
export const Fact = z.object({
  /** The factual claim — what the next agent needs to know */
  claim: z.string().min(1),
  /** Where this fact came from */
  source: SourceProvenance,
  /** Agent's confidence in this fact */
  confidence: ConfidenceLevel,
  /** Optional ID linking back to the originating session event */
  eventId: z.string().optional(),
});
export type Fact = z.infer<typeof Fact>;

// ─── Output Schema Registry ──────────────────────────────────────
export const OutputSchemaRef = z.object({
  /** Name of the registered output schema (e.g. "ComplianceDecisionV1") */
  schemaName: z.string().min(1),
  /** Version string for the schema */
  version: z.string().optional(),
});
export type OutputSchemaRef = z.infer<typeof OutputSchemaRef>;

// ─── Handoff Contract ───────────────────────────────────────────
export const HandoffContract = z.object({
  /** Unique identifier for this handoff (used for tracing) */
  handoffId: z.string().min(1),

  /** Which agent is receiving this contract */
  receivingAgent: z.string().min(1),

  /** The precise task for the receiving agent */
  task: z.string().min(1).max(500),

  /** Facts the receiving agent is allowed to see */
  facts: z.array(Fact).max(100).default([]),

  /** Context categories that were deliberately excluded */
  excludedContext: z.array(z.string()).default([]),

  /** Tools the receiving agent is permitted to call */
  allowedTools: z.array(z.string()).default([]),

  /** Tools the receiving agent must NOT call */
  forbiddenTools: z.array(z.string()).default([]),

  /** Reference to the expected output schema */
  outputSchema: OutputSchemaRef.optional(),

  /** Contract validity window in minutes from creation */
  expiresAfterMinutes: z.number().positive().max(1440).default(30),

  /** Optional escalation rule if the agent cannot complete the task */
  escalationRule: z.string().optional(),

  /** When this contract was created (ISO-8601) */
  createdAt: z.string().datetime(),

  /** Trace ID for observability linkage */
  traceId: z.string().min(1),
});
export type HandoffContract = z.infer<typeof HandoffContract>;

// ─── Session Event (input to the context compiler) ─────────────
export const SessionEventType = z.enum([
  "brainstorm",
  "tool_call",
  "tool_result",
  "llm_response",
  "user_message",
  "assistant_message",
  "decision",
  "internal_note",
]);
export type SessionEventType = z.infer<typeof SessionEventType>;

export const SessionEvent = z.object({
  id: z.string(),
  type: SessionEventType,
  timestamp: z.string().datetime(),
  content: z.string(),
  /** If this event should be excluded from handoff contracts */
  excludeFromHandoff: z.boolean().default(false),
  /** If newer than `maxAgeMinutes`, the event is not stale */
  maxAgeMinutes: z.number().positive().optional(),
  /** Which tool was called (for tool_call events) */
  toolName: z.string().optional(),
  /** Whether this event was a success */
  success: z.boolean().optional(),
});
export type SessionEvent = z.infer<typeof SessionEvent>;
