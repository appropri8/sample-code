/**
 * Policy Evaluator
 * 
 * Evaluates tool call requests against policy rules.
 * Returns: allow, deny, require_approval, or downgrade.
 */

import { TOOL_REGISTRY, requiresApproval, isToolAllowed, TOOL_TRUST_LEVELS } from "./1-tool-registry";

export interface PolicyRequest {
    user_id: string;
    run_id: string;
    tool: string;
    scope: string;
    resource: string;
    run_risk_tier: "low" | "medium" | "high";
}

export type PolicyDecision = "allow" | "deny" | "require_approval" | "downgrade";

export interface PolicyResult {
    decision: PolicyDecision;
    reason: string;
    rule_id: string;
    alternative_tool?: string; // For downgrades
}

export function evaluatePolicy(request: PolicyRequest): PolicyResult {
    // Rule 1: Deny dangerous tools for high-risk runs
    if (
        request.run_risk_tier === "high" &&
        TOOL_TRUST_LEVELS.dangerous.includes(request.tool)
    ) {
        return {
            decision: "deny",
            reason: "Dangerous tool not allowed for high-risk runs",
            rule_id: "rule-001",
        };
    }

    // Rule 2: Require approval for write operations
    if (request.scope === "write" && requiresApproval(request.tool)) {
        return {
            decision: "require_approval",
            reason: "Write operation requires human approval",
            rule_id: "rule-002",
        };
    }

    // Rule 3: Check resource constraints
    if (!isToolAllowed(request.tool, request.resource)) {
        return {
            decision: "deny",
            reason: `Resource ${request.resource} not in allowed constraints`,
            rule_id: "rule-003",
        };
    }

    // Rule 4: Downgrade write to read if possible for medium-risk runs
    if (request.scope === "write" && request.run_risk_tier === "medium") {
        const readTool = request.tool.replace(".write", ".read");
        if (TOOL_REGISTRY[readTool]) {
            return {
                decision: "downgrade",
                reason: "Downgrading write to read for medium-risk run",
                rule_id: "rule-004",
                alternative_tool: readTool,
            };
        }
    }

    // Rule 5: Check if tool exists
    if (!TOOL_REGISTRY[request.tool]) {
        return {
            decision: "deny",
            reason: `Unknown tool: ${request.tool}`,
            rule_id: "rule-005",
        };
    }

    // Default: allow
    return {
        decision: "allow",
        reason: "Request meets all policy requirements",
        rule_id: "rule-000",
    };
}

// Example usage
if (require.main === module) {
    console.log("=== Policy Evaluator Example ===\n");

    const scenarios: Array<{ name: string; request: PolicyRequest }> = [
        {
            name: "Legitimate read operation",
            request: {
                user_id: "user-123",
                run_id: "run-456",
                tool: "repo.read",
                scope: "read",
                resource: "/src/main.ts",
                run_risk_tier: "low",
            },
        },
        {
            name: "Dangerous tool on high-risk run",
            request: {
                user_id: "user-123",
                run_id: "run-789",
                tool: "repo.delete",
                scope: "write",
                resource: "/src",
                run_risk_tier: "high",
            },
        },
        {
            name: "Write operation requiring approval",
            request: {
                user_id: "user-123",
                run_id: "run-456",
                tool: "repo.write",
                scope: "write",
                resource: "/src/config.ts",
                run_risk_tier: "low",
            },
        },
        {
            name: "Access outside allowed prefixes",
            request: {
                user_id: "user-123",
                run_id: "run-456",
                tool: "repo.read",
                scope: "read",
                resource: "/etc/passwd",
                run_risk_tier: "low",
            },
        },
        {
            name: "Write downgraded to read (medium risk)",
            request: {
                user_id: "user-123",
                run_id: "run-456",
                tool: "repo.write",
                scope: "write",
                resource: "/src/main.ts",
                run_risk_tier: "medium",
            },
        },
        {
            name: "Unknown tool",
            request: {
                user_id: "user-123",
                run_id: "run-456",
                tool: "unknown.tool",
                scope: "read",
                resource: "/src",
                run_risk_tier: "low",
            },
        },
    ];

    scenarios.forEach((scenario, index) => {
        console.log(`${index + 1}. ${scenario.name}:`);
        console.log(`   Tool: ${scenario.request.tool}`);
        console.log(`   Resource: ${scenario.request.resource}`);
        console.log(`   Risk tier: ${scenario.request.run_risk_tier}`);

        const result = evaluatePolicy(scenario.request);

        const icon = result.decision === "allow" ? "✓" : "✗";
        console.log(`   ${icon} Decision: ${result.decision.toUpperCase()}`);
        console.log(`   Reason: ${result.reason}`);
        console.log(`   Rule: ${result.rule_id}`);

        if (result.alternative_tool) {
            console.log(`   Alternative: ${result.alternative_tool}`);
        }

        console.log();
    });
}
