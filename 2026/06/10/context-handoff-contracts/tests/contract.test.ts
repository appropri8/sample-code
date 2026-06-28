// ─── Validator Tests ────────────────────────────────────────────

describe("Validator", () => {
  it("passes a valid contract", () => {
    const contract = HandoffContract.parse({
      handoffId: "valid-001",
      receivingAgent: "TestAgent",
      task: "Do something",
      facts: [
        {
          claim: "A fact",
          source: { source: "test", timestamp: new Date().toISOString(), method: "test" },
          confidence: "high",
        },
      ],
      excludedContext: [],
      allowedTools: ["tool.a"],
      forbiddenTools: [],
      expiresAfterMinutes: 30,
      createdAt: new Date().toISOString(),
      traceId: "trace-valid",
    });

    const result = validateContract(contract);
    expect(result.valid).toBe(true);
    expect(result.errors).toHaveLength(0);
  });

  it("catches missing traceId", () => {
    const contract = {
      handoffId: "no-trace",
      receivingAgent: "TestAgent",
      task: "task",
      facts: [],
      excludedContext: [],
      allowedTools: [],
      forbiddenTools: [],
      expiresAfterMinutes: 30,
      createdAt: new Date().toISOString(),
      traceId: "",
    };

    const result = validateContract(contract);
    expect(result.valid).toBe(false);
    expect(result.errors.some((e) => e.includes("traceId"))).toBe(true);
  });

  it("catches facts missing source provenance", () => {
    const contract = {
      handoffId: "no-source",
      receivingAgent: "TestAgent",
      task: "task",
      facts: [
        {
          claim: "Some claim without source",
          source: { source: "", timestamp: new Date().toISOString() },
          confidence: "high",
        },
      ],
      excludedContext: [],
      allowedTools: ["tool.a"],
      forbiddenTools: [],
      expiresAfterMinutes: 30,
      createdAt: new Date().toISOString(),
      traceId: "trace-nosource",
    };

    const result = validateContract(contract);
    expect(result.valid).toBe(false);
    // Zod catches empty source string before custom checks
    expect(result.errors.some((e) => e.includes("source.source"))).toBe(true);
  });

  it("catches tools in both allowed and forbidden", () => {
    const contract = HandoffContract.parse({
      handoffId: "conflict",
      receivingAgent: "TestAgent",
      task: "task",
      facts: [],
      excludedContext: [],
      allowedTools: ["email.send"],
      forbiddenTools: ["email.send"],
      expiresAfterMinutes: 30,
      createdAt: new Date().toISOString(),
      traceId: "trace-conflict",
    });

    const result = validateContract(contract);
    expect(result.valid).toBe(false);
    expect(result.errors.some((e) => e.includes("allowedTools and forbiddenTools"))).toBe(true);
  });

  it("warns when contract has zero facts", () => {
    const contract = HandoffContract.parse({
      handoffId: "no-facts",
      receivingAgent: "TestAgent",
      task: "task",
      facts: [],
      excludedContext: [],
      allowedTools: [],
      forbiddenTools: [],
      expiresAfterMinutes: 30,
      createdAt: new Date().toISOString(),
      traceId: "trace-nofacts",
    });

    const result = validateContract(contract);
    expect(result.valid).toBe(true);
    expect(result.warnings.some((w) => w.includes("zero facts"))).toBe(true);
  });
});

// ─── Integration Tests ──────────────────────────────────────────

describe("Integration: compile → validate pipeline", () => {
  it("compiles a contract from mixed events and validates it successfully", () => {
    const events = [
      makeEvent({ type: "user_message", content: "Check if we can send this email to ACME." }),
      freshResult,
      staleResult,
      brainstormingNote,
      llmResponse,
    ];

    const contract = compileHandoffContract(
      "integ-001",
      "ComplianceReviewAgent",
      "Evaluate whether the proposed outbound email violates internal policy.",
      events,
      { maxResultAgeMinutes: 30 },
    );

    const validation = validateContract(contract);
    expect(validation.valid).toBe(true);

    const claims = contract.facts.map((f) => f.claim);
    expect(claims).toContain("Customer ACME Corp is an existing enterprise customer.");
    expect(claims).not.toContain("Pricing tier: legacy-2019");
    expect(claims).not.toContain("What if we just ignore the compliance check?");

    expect(contract.excludedContext.length).toBeGreaterThan(0);
    expect(contract.traceId).toBeTruthy();
  });
});

import { HandoffContract, SessionEvent } from "../src/schema";
import { compileHandoffContract } from "../src/context-compiler";
import { validateContract } from "../src/validator";

// ─── Fixtures ─────────────────────────────────────────────────────

function makeEvent(overrides: Partial<SessionEvent> = {}): SessionEvent {
  return {
    id: `evt-${Math.random().toString(36).slice(2, 8)}`,
    type: "user_message",
    timestamp: new Date().toISOString(),
    content: "test event",
    excludeFromHandoff: false,
    ...overrides,
  };
}

const freshResult = makeEvent({
  type: "tool_result",
  toolName: "crm.lookup_customer",
  content: "Customer ACME Corp is an existing enterprise customer.",
  maxAgeMinutes: 60,
  success: true,
});

const staleResult = makeEvent({
  id: "evt-stale",
  type: "tool_result",
  toolName: "crm.lookup_pricing",
  content: "Pricing tier: legacy-2019",
  timestamp: new Date(Date.now() - 120 * 60 * 1000).toISOString(),
  maxAgeMinutes: 30,
  success: true,
});

const brainstormingNote = makeEvent({
  id: "evt-brainstorm",
  type: "brainstorm",
  content: "What if we just ignore the compliance check?",
  excludeFromHandoff: true,
});

const internalNote = makeEvent({
  id: "evt-internal",
  type: "internal_note",
  content: "User seemed frustrated. Might churn.",
  excludeFromHandoff: true,
});

const sensitiveDecision = makeEvent({
  id: "evt-sensitive",
  type: "decision",
  content: "Rejected assumption: pricing is the only factor.",
  excludeFromHandoff: true,
});

const llmResponse = makeEvent({
  type: "llm_response",
  content: "The proposed email appears compliant with GDPR.",
});

// ─── Schema Tests ────────────────────────────────────────────────

describe("HandoffContract schema", () => {
  it("accepts a valid contract", () => {
    const contract = {
      handoffId: "risk-review-2026-001",
      receivingAgent: "ComplianceReviewAgent",
      task: "Evaluate whether the proposed outbound email violates internal policy.",
      facts: [
        {
          claim: "The recipient is an existing enterprise customer.",
          source: {
            source: "crm.lookup_customer",
            timestamp: new Date().toISOString(),
            method: "api_call",
          },
          confidence: "high" as const,
        },
      ],
      excludedContext: ["internal brainstorming notes"],
      allowedTools: ["policy.search", "crm.read_customer_status"],
      forbiddenTools: ["email.send"],
      expiresAfterMinutes: 30,
      createdAt: new Date().toISOString(),
      traceId: "trace-abc-123",
    };

    const result = HandoffContract.safeParse(contract);
    expect(result.success).toBe(true);
  });

  it("rejects a contract missing required fields", () => {
    const result = HandoffContract.safeParse({
      handoffId: "test",
    });
    expect(result.success).toBe(false);
  });
});

// ─── Context Compiler Tests ──────────────────────────────────────

describe("Context Compiler", () => {
  it("excludes events marked excludeFromHandoff", () => {
    const events = [freshResult, brainstormingNote, sensitiveDecision];
    const contract = compileHandoffContract(
      "test-001",
      "ComplianceReviewAgent",
      "Review compliance",
      events,
    );

    const claims = contract.facts.map((f) => f.claim);
    expect(claims).not.toContain("What if we just ignore the compliance check?");
    expect(claims).not.toContain("Rejected assumption: pricing is the only factor.");
  });

  it("excludes events by type (brainstorm, internal_note)", () => {
    const events = [freshResult, brainstormingNote, internalNote];
    const contract = compileHandoffContract(
      "test-002",
      "ComplianceReviewAgent",
      "Review compliance",
      events,
    );

    const claims = contract.facts.map((f) => f.claim);
    expect(claims).not.toContain("What if we just ignore the compliance check?");
    expect(claims).not.toContain("User seemed frustrated. Might churn.");
  });

  it("rejects stale tool results", () => {
    const events = [freshResult, staleResult];
    const contract = compileHandoffContract(
      "test-003",
      "ComplianceReviewAgent",
      "Review compliance",
      events,
      { maxResultAgeMinutes: 30 },
    );

    const claims = contract.facts.map((f) => f.claim);
    expect(claims).toContain("Customer ACME Corp is an existing enterprise customer.");
    expect(claims).not.toContain("Pricing tier: legacy-2019");
  });

  it("marks excluded context labels correctly", () => {
    const events = [freshResult, brainstormingNote, sensitiveDecision, staleResult];
    const contract = compileHandoffContract(
      "test-004",
      "ComplianceReviewAgent",
      "Review compliance",
      events,
      { maxResultAgeMinutes: 30 },
    );

    expect(contract.excludedContext).toContain("explicit:brainstorm");
    expect(contract.excludedContext).toContain("explicit:decision");
  });

  it("extracts facts from tool results and LLM responses", () => {
    const events = [freshResult, llmResponse];
    const contract = compileHandoffContract(
      "test-005",
      "ComplianceReviewAgent",
      "Review compliance",
      events,
    );

    const claims = contract.facts.map((f) => f.claim);
    expect(claims).toContain("Customer ACME Corp is an existing enterprise customer.");
    expect(claims).toContain("The proposed email appears compliant with GDPR.");
  });

  it("sets provenance metadata on facts", () => {
    const events = [freshResult];
    const contract = compileHandoffContract(
      "test-006",
      "ComplianceReviewAgent",
      "Review compliance",
      events,
    );

    const fact = contract.facts[0];
    expect(fact.source.source).toBe("crm.lookup_customer");
    expect(fact.confidence).toBe("high");
    expect(fact.eventId).toBe(freshResult.id);
  });
});
