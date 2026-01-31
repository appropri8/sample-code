/**
 * Unit Tests for Policy Rules
 * 
 * Tests each policy rule in isolation.
 */

import { describe, it, expect } from "vitest";
import { evaluatePolicy, PolicyRequest } from "../src/3-policy-evaluator";

describe("Policy Evaluator", () => {
    it("should deny dangerous tools for high-risk runs", () => {
        const request: PolicyRequest = {
            user_id: "user-123",
            run_id: "run-456",
            tool: "repo.delete",
            scope: "write",
            resource: "/src",
            run_risk_tier: "high",
        };

        const result = evaluatePolicy(request);

        expect(result.decision).toBe("deny");
        expect(result.rule_id).toBe("rule-001");
        expect(result.reason).toContain("Dangerous tool");
    });

    it("should require approval for write operations", () => {
        const request: PolicyRequest = {
            user_id: "user-123",
            run_id: "run-456",
            tool: "repo.write",
            scope: "write",
            resource: "/src/main.ts",
            run_risk_tier: "low",
        };

        const result = evaluatePolicy(request);

        expect(result.decision).toBe("require_approval");
        expect(result.rule_id).toBe("rule-002");
        expect(result.reason).toContain("requires human approval");
    });

    it("should deny access outside allowed prefixes", () => {
        const request: PolicyRequest = {
            user_id: "user-123",
            run_id: "run-456",
            tool: "repo.read",
            scope: "read",
            resource: "/etc/passwd",
            run_risk_tier: "low",
        };

        const result = evaluatePolicy(request);

        expect(result.decision).toBe("deny");
        expect(result.rule_id).toBe("rule-003");
        expect(result.reason).toContain("not in allowed constraints");
    });

    it("should downgrade write to read for medium-risk runs", () => {
        const request: PolicyRequest = {
            user_id: "user-123",
            run_id: "run-456",
            tool: "repo.write",
            scope: "write",
            resource: "/src/main.ts",
            run_risk_tier: "medium",
        };

        const result = evaluatePolicy(request);

        expect(result.decision).toBe("downgrade");
        expect(result.alternative_tool).toBe("repo.read");
        expect(result.rule_id).toBe("rule-004");
    });

    it("should deny unknown tools", () => {
        const request: PolicyRequest = {
            user_id: "user-123",
            run_id: "run-456",
            tool: "unknown.tool",
            scope: "read",
            resource: "/src",
            run_risk_tier: "low",
        };

        const result = evaluatePolicy(request);

        expect(result.decision).toBe("deny");
        expect(result.rule_id).toBe("rule-005");
        expect(result.reason).toContain("Unknown tool");
    });

    it("should allow safe operations", () => {
        const request: PolicyRequest = {
            user_id: "user-123",
            run_id: "run-456",
            tool: "repo.read",
            scope: "read",
            resource: "/src/main.ts",
            run_risk_tier: "low",
        };

        const result = evaluatePolicy(request);

        expect(result.decision).toBe("allow");
        expect(result.rule_id).toBe("rule-000");
    });

    it("should allow moderate tools for low-risk runs", () => {
        const request: PolicyRequest = {
            user_id: "user-123",
            run_id: "run-456",
            tool: "ticket.create",
            scope: "write",
            resource: "proj-123",
            run_risk_tier: "low",
        };

        const result = evaluatePolicy(request);

        expect(result.decision).toBe("allow");
    });

    it("should deny ticket operations on unauthorized projects", () => {
        const request: PolicyRequest = {
            user_id: "user-123",
            run_id: "run-456",
            tool: "ticket.create",
            scope: "write",
            resource: "proj-999",
            run_risk_tier: "low",
        };

        const result = evaluatePolicy(request);

        expect(result.decision).toBe("deny");
        expect(result.rule_id).toBe("rule-003");
    });
});
