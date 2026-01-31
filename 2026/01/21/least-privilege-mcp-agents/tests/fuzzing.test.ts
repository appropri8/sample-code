/**
 * Fuzzing Tests
 * 
 * Tests edge cases, encoding tricks, and malformed inputs.
 */

import { describe, it, expect } from "vitest";
import { evaluatePolicy, PolicyRequest } from "../src/3-policy-evaluator";

describe("Fuzzing", () => {
    it("should handle path traversal attempts", () => {
        const traversalPaths = [
            "/src/../../../etc/passwd",
            "/src/../../etc/passwd",
            "/src/./../etc/passwd",
            "/../etc/passwd",
            "/src/./../../etc/passwd",
        ];

        traversalPaths.forEach((path) => {
            const request: PolicyRequest = {
                user_id: "user-123",
                run_id: "run-456",
                tool: "repo.read",
                scope: "read",
                resource: path,
                run_risk_tier: "low",
            };

            const result = evaluatePolicy(request);

            expect(result.decision).toBe("deny");
            expect(result.rule_id).toBe("rule-003");
        });
    });

    it("should handle URL-encoded paths", () => {
        const encodedPaths = [
            "/src/%2e%2e/%2e%2e/etc/passwd",
            "/src/%2e%2e%2f%2e%2e%2fetc%2fpasswd",
            "/src/%252e%252e/%252e%252e/etc/passwd",
        ];

        encodedPaths.forEach((path) => {
            const request: PolicyRequest = {
                user_id: "user-123",
                run_id: "run-456",
                tool: "repo.read",
                scope: "read",
                resource: path,
                run_risk_tier: "low",
            };

            const result = evaluatePolicy(request);

            // URL-encoded paths should not match allowed prefixes
            expect(result.decision).toBe("deny");
        });
    });

    it("should handle null bytes", () => {
        const nullBytePaths = [
            "/src/main.ts\x00.txt",
            "/src\x00/../../etc/passwd",
            "/src/main\x00.ts",
        ];

        nullBytePaths.forEach((path) => {
            const request: PolicyRequest = {
                user_id: "user-123",
                run_id: "run-456",
                tool: "repo.read",
                scope: "read",
                resource: path,
                run_risk_tier: "low",
            };

            const result = evaluatePolicy(request);

            // Null bytes should not bypass checks
            expect(result.decision).toBe("deny");
        });
    });

    it("should handle empty strings", () => {
        const request: PolicyRequest = {
            user_id: "user-123",
            run_id: "run-456",
            tool: "repo.read",
            scope: "read",
            resource: "",
            run_risk_tier: "low",
        };

        const result = evaluatePolicy(request);

        expect(result.decision).toBe("deny");
    });

    it("should handle very long paths", () => {
        const longPath = "/src/" + "a".repeat(10000);

        const request: PolicyRequest = {
            user_id: "user-123",
            run_id: "run-456",
            tool: "repo.read",
            scope: "read",
            resource: longPath,
            run_risk_tier: "low",
        };

        const result = evaluatePolicy(request);

        // Should still check prefix correctly
        expect(result.decision).toBe("allow");
    });

    it("should handle special characters in paths", () => {
        const specialPaths = [
            "/src/file with spaces.ts",
            "/src/file'with'quotes.ts",
            '/src/file"with"doublequotes.ts',
            "/src/file;with;semicolons.ts",
            "/src/file&with&ampersands.ts",
        ];

        specialPaths.forEach((path) => {
            const request: PolicyRequest = {
                user_id: "user-123",
                run_id: "run-456",
                tool: "repo.read",
                scope: "read",
                resource: path,
                run_risk_tier: "low",
            };

            const result = evaluatePolicy(request);

            // Special characters in allowed paths should be allowed
            expect(result.decision).toBe("allow");
        });
    });

    it("should handle case sensitivity", () => {
        const casePaths = [
            "/SRC/main.ts",
            "/Src/main.ts",
            "/src/MAIN.TS",
        ];

        casePaths.forEach((path) => {
            const request: PolicyRequest = {
                user_id: "user-123",
                run_id: "run-456",
                tool: "repo.read",
                scope: "read",
                resource: path,
                run_risk_tier: "low",
            };

            const result = evaluatePolicy(request);

            // Case-sensitive check: /SRC is not /src
            expect(result.decision).toBe("deny");
        });
    });

    it("should handle Unicode characters", () => {
        const unicodePaths = [
            "/src/文件.ts",
            "/src/файл.ts",
            "/src/ファイル.ts",
        ];

        unicodePaths.forEach((path) => {
            const request: PolicyRequest = {
                user_id: "user-123",
                run_id: "run-456",
                tool: "repo.read",
                scope: "read",
                resource: path,
                run_risk_tier: "low",
            };

            const result = evaluatePolicy(request);

            // Unicode in allowed paths should be allowed
            expect(result.decision).toBe("allow");
        });
    });

    it("should handle malformed tool names", () => {
        const malformedTools = [
            "",
            "repo.",
            ".read",
            "repo..read",
            "repo read",
            "repo\nread",
            "repo\tread",
        ];

        malformedTools.forEach((tool) => {
            const request: PolicyRequest = {
                user_id: "user-123",
                run_id: "run-456",
                tool,
                scope: "read",
                resource: "/src",
                run_risk_tier: "low",
            };

            const result = evaluatePolicy(request);

            expect(result.decision).toBe("deny");
            expect(result.rule_id).toBe("rule-005");
        });
    });

    it("should handle injection in user_id and run_id", () => {
        const injectionIds = [
            "user-123'; DROP TABLE users; --",
            "user-123<script>alert('xss')</script>",
            "user-123\n\nmalicious",
        ];

        injectionIds.forEach((id) => {
            const request: PolicyRequest = {
                user_id: id,
                run_id: "run-456",
                tool: "repo.read",
                scope: "read",
                resource: "/src/main.ts",
                run_risk_tier: "low",
            };

            const result = evaluatePolicy(request);

            // Policy should still evaluate correctly
            // (IDs are just logged, not used in policy logic)
            expect(result.decision).toBe("allow");
        });
    });
});
