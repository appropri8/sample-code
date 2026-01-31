/**
 * Server-Side Enforcement
 * 
 * MCP server checks token claims match the request.
 * Defense in depth - even if client is compromised, server protects.
 */

import jwt from "jsonwebtoken";
import { CapabilityToken } from "./2-capability-tokens";

const SECRET_KEY = process.env.JWT_SECRET || "demo-secret-key-change-in-production";

export function enforceTokenOnServer(
    toolName: string,
    resource: string,
    token: string
): void {
    // Verify and decode token
    let payload: CapabilityToken;
    try {
        payload = jwt.verify(token, SECRET_KEY) as CapabilityToken;
    } catch (error) {
        if (error instanceof jwt.TokenExpiredError) {
            throw new Error("Token has expired");
        }
        if (error instanceof jwt.JsonWebTokenError) {
            throw new Error("Invalid token signature");
        }
        throw error;
    }

    // Check tool matches
    if (payload.tool !== toolName) {
        throw new Error(
            `Token tool mismatch: token authorizes ${payload.tool}, but request is for ${toolName}`
        );
    }

    // Check resource matches
    if (!resource.startsWith(payload.resource)) {
        throw new Error(
            `Token resource mismatch: token authorizes ${payload.resource}, but request is for ${resource}`
        );
    }

    // Check expiration (redundant with jwt.verify, but explicit)
    const now = Math.floor(Date.now() / 1000);
    if (payload.exp < now) {
        throw new Error("Token has expired");
    }

    console.log(`   ✓ Server enforcement passed for ${toolName} on ${resource}`);
}

// Simulated MCP server tool execution
export function executeMCPTool(
    toolName: string,
    args: any,
    token: string
): any {
    console.log(`\n[MCP SERVER] Received tool call: ${toolName}`);
    console.log(`   Args:`, args);

    // Extract resource from args
    const resource = args.path || args.resource || args.project_id || "";

    // Enforce token
    try {
        enforceTokenOnServer(toolName, resource, token);
    } catch (error) {
        console.log(`   ✗ Server enforcement failed: ${(error as Error).message}`);
        throw error;
    }

    // Execute tool
    console.log(`   ✓ Executing ${toolName}...`);

    // Simulated tool execution
    switch (toolName) {
        case "repo.read":
            return { content: `Content of ${resource}`, size: 1024 };
        case "repo.write":
            return { success: true, path: resource };
        case "ticket.create":
            return { ticket_id: "TICKET-123", project: resource };
        default:
            return { result: "success" };
    }
}

// Example usage
if (require.main === module) {
    const { mintCapabilityToken } = require("./2-capability-tokens");

    console.log("=== Server-Side Enforcement Example ===\n");

    // Scenario 1: Valid request
    console.log("1. Valid request:");
    const validToken = mintCapabilityToken(
        "user-123",
        "run-456",
        "repo.read",
        "read",
        "/src"
    );

    try {
        const result = executeMCPTool(
            "repo.read",
            { path: "/src/main.ts" },
            validToken
        );
        console.log(`   Result:`, result);
    } catch (error) {
        console.log(`   Error: ${(error as Error).message}`);
    }

    // Scenario 2: Tool mismatch
    console.log("\n2. Tool mismatch:");
    const readToken = mintCapabilityToken(
        "user-123",
        "run-456",
        "repo.read",
        "read",
        "/src"
    );

    try {
        const result = executeMCPTool(
            "repo.write",
            { path: "/src/main.ts", content: "new content" },
            readToken
        );
        console.log(`   Result:`, result);
    } catch (error) {
        console.log(`   Error: ${(error as Error).message}`);
    }

    // Scenario 3: Resource mismatch
    console.log("\n3. Resource mismatch:");
    const srcToken = mintCapabilityToken(
        "user-123",
        "run-456",
        "repo.read",
        "read",
        "/src"
    );

    try {
        const result = executeMCPTool(
            "repo.read",
            { path: "/etc/passwd" },
            srcToken
        );
        console.log(`   Result:`, result);
    } catch (error) {
        console.log(`   Error: ${(error as Error).message}`);
    }

    // Scenario 4: Expired token
    console.log("\n4. Expired token:");
    const expiredToken = mintCapabilityToken(
        "user-123",
        "run-456",
        "repo.read",
        "read",
        "/src",
        -1 // Already expired
    );

    try {
        const result = executeMCPTool(
            "repo.read",
            { path: "/src/main.ts" },
            expiredToken
        );
        console.log(`   Result:`, result);
    } catch (error) {
        console.log(`   Error: ${(error as Error).message}`);
    }

    // Scenario 5: Invalid signature
    console.log("\n5. Invalid signature:");
    const tamperedToken = validToken.slice(0, -10) + "tampered123";

    try {
        const result = executeMCPTool(
            "repo.read",
            { path: "/src/main.ts" },
            tamperedToken
        );
        console.log(`   Result:`, result);
    } catch (error) {
        console.log(`   Error: ${(error as Error).message}`);
    }
}
