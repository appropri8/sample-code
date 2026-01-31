/**
 * MCP Tool-Call Interceptor
 * 
 * Client-side enforcement that wraps tool calls.
 * Checks for valid capability token before allowing execution.
 */

import { verifyCapabilityToken, CapabilityToken } from "./2-capability-tokens";

interface ToolCallResult {
    success: boolean;
    data?: any;
    error?: string;
}

// Simulated tool execution
function executeToolOnServer(toolName: string, args: any): any {
    console.log(`   [SERVER] Executing ${toolName} with args:`, args);
    return { result: "success", data: `Result from ${toolName}` };
}

// Policy decision logger
function logPolicyDecision(
    tool: string,
    userId: string,
    runId: string,
    decision: "allow" | "deny",
    reason: string,
    ruleId: string
): void {
    const log = {
        timestamp: new Date().toISOString(),
        user_id: userId,
        run_id: runId,
        tool,
        decision,
        reason,
        rule_id: ruleId,
    };
    console.log(`   [AUDIT] ${JSON.stringify(log)}`);
}

export async function interceptToolCall(
    toolName: string,
    args: any,
    capabilityToken: string
): Promise<ToolCallResult> {
    console.log(`\n[INTERCEPTOR] Tool call: ${toolName}`);

    // Verify token
    let tokenPayload: CapabilityToken;
    try {
        tokenPayload = verifyCapabilityToken(capabilityToken);
    } catch (error) {
        const errorMsg = (error as Error).message;
        console.log(`   ✗ Token verification failed: ${errorMsg}`);

        logPolicyDecision(
            toolName,
            "unknown",
            "unknown",
            "deny",
            errorMsg,
            "interceptor-001"
        );

        return {
            success: false,
            error: "Invalid capability token",
        };
    }

    // Check token matches request
    if (tokenPayload.tool !== toolName) {
        console.log(`   ✗ Token tool mismatch: expected ${toolName}, got ${tokenPayload.tool}`);

        logPolicyDecision(
            toolName,
            tokenPayload.sub,
            tokenPayload.run_id,
            "deny",
            "Token tool mismatch",
            "interceptor-002"
        );

        return {
            success: false,
            error: "Token does not authorize this tool",
        };
    }

    // Check resource constraint (if applicable)
    const resource = args.path || args.resource || args.project_id;
    if (resource && !resource.startsWith(tokenPayload.resource)) {
        console.log(`   ✗ Resource mismatch: ${resource} not allowed by token (${tokenPayload.resource})`);

        logPolicyDecision(
            toolName,
            tokenPayload.sub,
            tokenPayload.run_id,
            "deny",
            "Resource not allowed by token",
            "interceptor-003"
        );

        return {
            success: false,
            error: "Token does not authorize this resource",
        };
    }

    // Log successful authorization
    console.log(`   ✓ Token valid for ${toolName}`);
    logPolicyDecision(
        toolName,
        tokenPayload.sub,
        tokenPayload.run_id,
        "allow",
        "Valid capability token",
        "interceptor-000"
    );

    // Execute tool call
    try {
        const result = executeToolOnServer(toolName, args);
        return {
            success: true,
            data: result,
        };
    } catch (error) {
        return {
            success: false,
            error: (error as Error).message,
        };
    }
}

// Example usage
if (require.main === module) {
    const { mintCapabilityToken } = require("./2-capability-tokens");

    console.log("=== Tool Call Interceptor Example ===\n");

    // Scenario 1: Valid token
    console.log("1. Valid token for repo.read:");
    const validToken = mintCapabilityToken(
        "user-123",
        "run-456",
        "repo.read",
        "read",
        "/src"
    );

    interceptToolCall("repo.read", { path: "/src/main.ts" }, validToken)
        .then((result) => {
            if (result.success) {
                console.log(`   ✓ Tool call succeeded`);
            } else {
                console.log(`   ✗ Tool call failed: ${result.error}`);
            }
        });

    // Scenario 2: Invalid token
    setTimeout(() => {
        console.log("\n2. Invalid token:");
        interceptToolCall("repo.read", { path: "/src/main.ts" }, "invalid-token")
            .then((result) => {
                if (result.success) {
                    console.log(`   ✓ Tool call succeeded`);
                } else {
                    console.log(`   ✗ Tool call failed: ${result.error}`);
                }
            });
    }, 100);

    // Scenario 3: Token tool mismatch
    setTimeout(() => {
        console.log("\n3. Token tool mismatch:");
        const readToken = mintCapabilityToken(
            "user-123",
            "run-456",
            "repo.read",
            "read",
            "/src"
        );

        interceptToolCall("repo.write", { path: "/src/main.ts" }, readToken)
            .then((result) => {
                if (result.success) {
                    console.log(`   ✓ Tool call succeeded`);
                } else {
                    console.log(`   ✗ Tool call failed: ${result.error}`);
                }
            });
    }, 200);

    // Scenario 4: Resource mismatch
    setTimeout(() => {
        console.log("\n4. Resource mismatch:");
        const srcToken = mintCapabilityToken(
            "user-123",
            "run-456",
            "repo.read",
            "read",
            "/src"
        );

        interceptToolCall("repo.read", { path: "/etc/passwd" }, srcToken)
            .then((result) => {
                if (result.success) {
                    console.log(`   ✓ Tool call succeeded`);
                } else {
                    console.log(`   ✗ Tool call failed: ${result.error}`);
                }
            });
    }, 300);
}
