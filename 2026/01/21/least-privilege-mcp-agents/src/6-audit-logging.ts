/**
 * Audit Logging and Queries
 * 
 * Logs all policy decisions and provides query functions.
 * Creates an audit trail for security monitoring.
 */

import { PolicyRequest, PolicyResult } from "./3-policy-evaluator";

export interface PolicyDecisionLog {
    timestamp: string;
    user_id: string;
    run_id: string;
    tool: string;
    scope: string;
    resource: string;
    decision: "allow" | "deny" | "require_approval" | "downgrade";
    reason: string;
    rule_id: string;
    token_id?: string;
}

// In-memory log storage (in production, use a database or logging service)
const AUDIT_LOGS: PolicyDecisionLog[] = [];

export function logPolicyDecision(
    request: PolicyRequest,
    result: PolicyResult,
    tokenId?: string
): void {
    const log: PolicyDecisionLog = {
        timestamp: new Date().toISOString(),
        user_id: request.user_id,
        run_id: request.run_id,
        tool: request.tool,
        scope: request.scope,
        resource: request.resource,
        decision: result.decision,
        reason: result.reason,
        rule_id: result.rule_id,
        token_id: tokenId,
    };

    AUDIT_LOGS.push(log);

    // In production: send to logging service
    // await sendToLoggingService(log);

    console.log(`[AUDIT] ${JSON.stringify(log)}`);
}

// Query functions

export function queryLogs(filters: Partial<PolicyDecisionLog>): PolicyDecisionLog[] {
    return AUDIT_LOGS.filter((log) => {
        for (const [key, value] of Object.entries(filters)) {
            if (log[key as keyof PolicyDecisionLog] !== value) {
                return false;
            }
        }
        return true;
    });
}

export function queryDeniedWrites(hours: number = 24): PolicyDecisionLog[] {
    const cutoff = new Date(Date.now() - hours * 60 * 60 * 1000).toISOString();

    return AUDIT_LOGS.filter(
        (log) =>
            log.scope === "write" &&
            log.decision === "deny" &&
            log.timestamp >= cutoff
    );
}

export function queryHighRiskRuns(): PolicyDecisionLog[] {
    // Get unique run IDs with denied dangerous tools
    const highRiskRunIds = new Set(
        AUDIT_LOGS.filter(
            (log) =>
                log.decision === "deny" &&
                log.rule_id === "rule-001" // Dangerous tool on high-risk run
        ).map((log) => log.run_id)
    );

    // Get all logs for those runs
    return AUDIT_LOGS.filter((log) => highRiskRunIds.has(log.run_id));
}

export function queryPendingApprovals(): PolicyDecisionLog[] {
    return AUDIT_LOGS.filter((log) => log.decision === "require_approval");
}

export function queryByUser(userId: string): PolicyDecisionLog[] {
    return AUDIT_LOGS.filter((log) => log.user_id === userId);
}

export function queryByRun(runId: string): PolicyDecisionLog[] {
    return AUDIT_LOGS.filter((log) => log.run_id === runId);
}

export function getDecisionStats(): {
    total: number;
    allowed: number;
    denied: number;
    require_approval: number;
    downgraded: number;
} {
    const stats = {
        total: AUDIT_LOGS.length,
        allowed: 0,
        denied: 0,
        require_approval: 0,
        downgraded: 0,
    };

    AUDIT_LOGS.forEach((log) => {
        switch (log.decision) {
            case "allow":
                stats.allowed++;
                break;
            case "deny":
                stats.denied++;
                break;
            case "require_approval":
                stats.require_approval++;
                break;
            case "downgrade":
                stats.downgraded++;
                break;
        }
    });

    return stats;
}

export function clearLogs(): void {
    AUDIT_LOGS.length = 0;
}

// Example usage
if (require.main === module) {
    const { evaluatePolicy } = require("./3-policy-evaluator");

    console.log("=== Audit Logging Example ===\n");

    // Generate some sample logs
    console.log("1. Generating sample audit logs...\n");

    const sampleRequests: PolicyRequest[] = [
        {
            user_id: "user-123",
            run_id: "run-001",
            tool: "repo.read",
            scope: "read",
            resource: "/src/main.ts",
            run_risk_tier: "low",
        },
        {
            user_id: "user-123",
            run_id: "run-001",
            tool: "repo.write",
            scope: "write",
            resource: "/src/config.ts",
            run_risk_tier: "low",
        },
        {
            user_id: "user-456",
            run_id: "run-002",
            tool: "repo.delete",
            scope: "write",
            resource: "/",
            run_risk_tier: "high",
        },
        {
            user_id: "user-456",
            run_id: "run-002",
            tool: "repo.read",
            scope: "read",
            resource: "/etc/passwd",
            run_risk_tier: "high",
        },
        {
            user_id: "user-789",
            run_id: "run-003",
            tool: "repo.write",
            scope: "write",
            resource: "/src/main.ts",
            run_risk_tier: "medium",
        },
    ];

    sampleRequests.forEach((request) => {
        const result = evaluatePolicy(request);
        logPolicyDecision(request, result);
    });

    // Query examples
    console.log("\n2. Query: All denied write operations:");
    const deniedWrites = queryDeniedWrites();
    console.log(`   Found ${deniedWrites.length} denied writes`);
    deniedWrites.forEach((log) => {
        console.log(`   - ${log.tool} on ${log.resource}: ${log.reason}`);
    });

    console.log("\n3. Query: High-risk runs:");
    const highRiskRuns = queryHighRiskRuns();
    console.log(`   Found ${highRiskRuns.length} logs from high-risk runs`);
    highRiskRuns.forEach((log) => {
        console.log(`   - Run ${log.run_id}: ${log.tool} ${log.decision}`);
    });

    console.log("\n4. Query: Pending approvals:");
    const pendingApprovals = queryPendingApprovals();
    console.log(`   Found ${pendingApprovals.length} pending approvals`);
    pendingApprovals.forEach((log) => {
        console.log(`   - ${log.tool} on ${log.resource} by ${log.user_id}`);
    });

    console.log("\n5. Query: Logs for user-123:");
    const userLogs = queryByUser("user-123");
    console.log(`   Found ${userLogs.length} logs for user-123`);
    userLogs.forEach((log) => {
        console.log(`   - ${log.tool}: ${log.decision}`);
    });

    console.log("\n6. Query: Logs for run-002:");
    const runLogs = queryByRun("run-002");
    console.log(`   Found ${runLogs.length} logs for run-002`);
    runLogs.forEach((log) => {
        console.log(`   - ${log.tool}: ${log.decision} (${log.reason})`);
    });

    console.log("\n7. Decision statistics:");
    const stats = getDecisionStats();
    console.log(`   Total: ${stats.total}`);
    console.log(`   Allowed: ${stats.allowed} (${((stats.allowed / stats.total) * 100).toFixed(1)}%)`);
    console.log(`   Denied: ${stats.denied} (${((stats.denied / stats.total) * 100).toFixed(1)}%)`);
    console.log(`   Require approval: ${stats.require_approval} (${((stats.require_approval / stats.total) * 100).toFixed(1)}%)`);
    console.log(`   Downgraded: ${stats.downgraded} (${((stats.downgraded / stats.total) * 100).toFixed(1)}%)`);
}
