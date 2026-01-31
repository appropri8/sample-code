/**
 * Capability Token Format
 * 
 * JWT-based tokens with specific claims for tool access.
 * Tokens are short-lived and specific to one tool, one resource, one run.
 */

import jwt from "jsonwebtoken";

const SECRET_KEY = process.env.JWT_SECRET || "demo-secret-key-change-in-production";

export interface CapabilityToken {
    sub: string;          // User ID
    run_id: string;       // Agent run ID
    tool: string;         // Tool name (e.g., "repo.read")
    scope: string;        // Scope (e.g., "read")
    resource: string;     // Resource constraint (e.g., "/src")
    exp: number;          // Expiration timestamp
    nonce: string;        // Unique nonce to prevent replay
}

// Token allowlist for revocation
const VALID_TOKENS = new Set<string>();

export function generateNonce(): string {
    return Math.random().toString(36).substring(2, 15) +
        Math.random().toString(36).substring(2, 15);
}

export function mintCapabilityToken(
    userId: string,
    runId: string,
    tool: string,
    scope: string,
    resource: string,
    ttlSeconds: number = 300 // 5 minutes default
): string {
    const payload: CapabilityToken = {
        sub: userId,
        run_id: runId,
        tool,
        scope,
        resource,
        exp: Math.floor(Date.now() / 1000) + ttlSeconds,
        nonce: generateNonce(),
    };

    const token = jwt.sign(payload, SECRET_KEY);
    VALID_TOKENS.add(token);

    return token;
}

export function verifyCapabilityToken(token: string): CapabilityToken {
    try {
        const payload = jwt.verify(token, SECRET_KEY) as CapabilityToken;

        // Check if token is in allowlist
        if (!VALID_TOKENS.has(token)) {
            throw new Error("Token has been revoked");
        }

        return payload;
    } catch (error) {
        if (error instanceof jwt.TokenExpiredError) {
            throw new Error("Token has expired");
        }
        if (error instanceof jwt.JsonWebTokenError) {
            throw new Error("Invalid token");
        }
        throw error;
    }
}

export function revokeToken(token: string): void {
    VALID_TOKENS.delete(token);
}

export function isTokenValid(token: string): boolean {
    return VALID_TOKENS.has(token);
}

export function decodeToken(token: string): CapabilityToken | null {
    try {
        return jwt.decode(token) as CapabilityToken;
    } catch {
        return null;
    }
}

// Example usage
if (require.main === module) {
    console.log("=== Capability Token Example ===\n");

    // 1. Mint a token
    console.log("1. Minting token for repo.read:");
    const token = mintCapabilityToken(
        "user-123",
        "run-456",
        "repo.read",
        "read",
        "/src",
        300 // 5 minutes
    );
    console.log(`   Token: ${token.substring(0, 50)}...`);

    // 2. Decode token (without verification)
    console.log("\n2. Decoded token payload:");
    const decoded = decodeToken(token);
    console.log(`   User: ${decoded?.sub}`);
    console.log(`   Run: ${decoded?.run_id}`);
    console.log(`   Tool: ${decoded?.tool}`);
    console.log(`   Scope: ${decoded?.scope}`);
    console.log(`   Resource: ${decoded?.resource}`);
    console.log(`   Expires: ${new Date((decoded?.exp || 0) * 1000).toISOString()}`);
    console.log(`   Nonce: ${decoded?.nonce}`);

    // 3. Verify token
    console.log("\n3. Verifying token:");
    try {
        const verified = verifyCapabilityToken(token);
        console.log(`   ✓ Token is valid`);
        console.log(`   Tool: ${verified.tool}`);
    } catch (error) {
        console.log(`   ✗ Token verification failed: ${error}`);
    }

    // 4. Check if token is in allowlist
    console.log("\n4. Checking allowlist:");
    console.log(`   Token in allowlist: ${isTokenValid(token)}`);

    // 5. Revoke token
    console.log("\n5. Revoking token:");
    revokeToken(token);
    console.log(`   Token revoked`);
    console.log(`   Token in allowlist: ${isTokenValid(token)}`);

    // 6. Try to verify revoked token
    console.log("\n6. Verifying revoked token:");
    try {
        verifyCapabilityToken(token);
        console.log(`   ✓ Token is valid`);
    } catch (error) {
        console.log(`   ✗ Token verification failed: ${(error as Error).message}`);
    }

    // 7. Mint token with short TTL
    console.log("\n7. Minting token with 1-second TTL:");
    const shortToken = mintCapabilityToken(
        "user-123",
        "run-456",
        "repo.read",
        "read",
        "/src",
        1 // 1 second
    );
    console.log(`   Token minted`);

    setTimeout(() => {
        console.log("\n8. Verifying expired token (after 2 seconds):");
        try {
            verifyCapabilityToken(shortToken);
            console.log(`   ✓ Token is valid`);
        } catch (error) {
            console.log(`   ✗ Token verification failed: ${(error as Error).message}`);
        }
    }, 2000);
}
