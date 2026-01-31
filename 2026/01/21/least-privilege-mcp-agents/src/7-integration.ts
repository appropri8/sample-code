/**
 * Full Integration Example
 * 
 * Complete end-to-end flow:
 * Agent → Policy Gate → MCP Server
 */

import { PolicyRequest, evaluatePolicy } from "./3-policy-evaluator";
import { mintCapabilityToken } from "./2-capability-tokens";
import { interceptToolCall } from "./4-tool-interceptor";
import { executeMCPTool } from "./5-server-enforcement";
import { logPolicyDecision } from "./6-audit-logging";

// Simulated agent that wants to call tools
class MCPAgent {
    constructor(
        private userId: string,
        private runId: string,
        private riskTier: "low" | "medium" | "high"
    ) { }

    async callTool(
        tool: string,
        scope: string,
        resource: string,
        args: any
    ): Promise<any> {
        console.log(`\n[AGENT] Requesting to call ${tool} on ${resource}`);

        // Step 1: Request capability from policy gate
        const policyRequest: PolicyRequest = {
            user_id: this.userId,
            run_id: this.runId,
            tool,
            scope,
            resource,
            run_risk_tier: this.riskTier,
        };

        console.log(`[POLICY GATE] Evaluating request...`);
        const policyResult = evaluatePolicy(policyRequest);

        // Log the decision
        logPolicyDecision(policyRequest, policyResult);

        // Step 2: Handle policy decision
        if (policyResult.decision === "deny") {
            console.log(`[POLICY GATE] ✗ DENIED: ${policyResult.reason}`);
            throw new Error(`Policy denied: ${policyResult.reason}`);
        }

        if (policyResult.decision === "require_approval") {
            console.log(`[POLICY GATE] ⏸ REQUIRES APPROVAL: ${policyResult.reason}`);
            throw new Error(`Requires human approval: ${policyResult.reason}`);
        }

        let actualTool = tool;
        if (policyResult.decision === "downgrade") {
            console.log(`[POLICY GATE] ⬇ DOWNGRADED to ${policyResult.alternative_tool}`);
            actualTool = policyResult.alternative_tool!;
        }

        // Step 3: Mint capability token
        console.log(`[POLICY GATE] ✓ ALLOWED - Minting capability token`);
        const token = mintCapabilityToken(
            this.userId,
            this.runId,
            actualTool,
            scope === "write" && policyResult.decision === "downgrade" ? "read" : scope,
            resource
        );

        // Step 4: Call tool through interceptor (client-side enforcement)
        console.log(`[CLIENT] Calling tool with capability token`);
        const interceptResult = await interceptToolCall(actualTool, args, token);

        if (!interceptResult.success) {
            throw new Error(`Interceptor blocked: ${interceptResult.error}`);
        }

        // Step 5: Execute on MCP server (server-side enforcement)
        const serverResult = executeMCPTool(actualTool, args, token);

        console.log(`[AGENT] ✓ Tool call succeeded`);
        return serverResult;
    }
}

// Example usage
if (require.main === module) {
    console.log("=== Full Integration Example ===\n");
    console.log("Demonstrating complete flow: Agent → Policy Gate → MCP Server\n");

    async function runScenarios() {
        // Scenario 1: Low-risk agent, legitimate read
        console.log("=".repeat(70));
        console.log("SCENARIO 1: Low-risk agent, legitimate read");
        console.log("=".repeat(70));

        const agent1 = new MCPAgent("user-123", "run-001", "low");
        try {
            const result = await agent1.callTool(
                "repo.read",
                "read",
                "/src",
                { path: "/src/main.ts" }
            );
            console.log(`Result:`, result);
        } catch (error) {
            console.log(`Failed: ${(error as Error).message}`);
        }

        // Scenario 2: Low-risk agent, write requiring approval
        console.log("\n" + "=".repeat(70));
        console.log("SCENARIO 2: Low-risk agent, write requiring approval");
        console.log("=".repeat(70));

        const agent2 = new MCPAgent("user-456", "run-002", "low");
        try {
            const result = await agent2.callTool(
                "repo.write",
                "write",
                "/src",
                { path: "/src/config.ts", content: "new config" }
            );
            console.log(`Result:`, result);
        } catch (error) {
            console.log(`Failed: ${(error as Error).message}`);
        }

        // Scenario 3: High-risk agent, dangerous tool (blocked)
        console.log("\n" + "=".repeat(70));
        console.log("SCENARIO 3: High-risk agent, dangerous tool (BLOCKED)");
        console.log("=".repeat(70));

        const agent3 = new MCPAgent("user-789", "run-003", "high");
        try {
            const result = await agent3.callTool(
                "repo.delete",
                "write",
                "/",
                { path: "/" }
            );
            console.log(`Result:`, result);
        } catch (error) {
            console.log(`Failed: ${(error as Error).message}`);
        }

        // Scenario 4: Medium-risk agent, write downgraded to read
        console.log("\n" + "=".repeat(70));
        console.log("SCENARIO 4: Medium-risk agent, write downgraded to read");
        console.log("=".repeat(70));

        const agent4 = new MCPAgent("user-123", "run-004", "medium");
        try {
            const result = await agent4.callTool(
                "repo.write",
                "write",
                "/src",
                { path: "/src/main.ts" }
            );
            console.log(`Result:`, result);
        } catch (error) {
            console.log(`Failed: ${(error as Error).message}`);
        }

        // Scenario 5: Path traversal attempt (blocked)
        console.log("\n" + "=".repeat(70));
        console.log("SCENARIO 5: Path traversal attempt (BLOCKED)");
        console.log("=".repeat(70));

        const agent5 = new MCPAgent("user-123", "run-005", "low");
        try {
            const result = await agent5.callTool(
                "repo.read",
                "read",
                "/src/../../../etc",
                { path: "/src/../../../etc/passwd" }
            );
            console.log(`Result:`, result);
        } catch (error) {
            console.log(`Failed: ${(error as Error).message}`);
        }

        // Summary
        console.log("\n" + "=".repeat(70));
        console.log("SUMMARY");
        console.log("=".repeat(70));

        const { getDecisionStats } = require("./6-audit-logging");
        const stats = getDecisionStats();

        console.log(`\nTotal requests: ${stats.total}`);
        console.log(`Allowed: ${stats.allowed} (${((stats.allowed / stats.total) * 100).toFixed(1)}%)`);
        console.log(`Denied: ${stats.denied} (${((stats.denied / stats.total) * 100).toFixed(1)}%)`);
        console.log(`Require approval: ${stats.require_approval} (${((stats.require_approval / stats.total) * 100).toFixed(1)}%)`);
        console.log(`Downgraded: ${stats.downgraded} (${((stats.downgraded / stats.total) * 100).toFixed(1)}%)`);

        console.log("\n✓ Integration example complete");
    }

    runScenarios().catch(console.error);
}
