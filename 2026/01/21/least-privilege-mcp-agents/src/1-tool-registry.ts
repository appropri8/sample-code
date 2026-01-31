/**
 * Tool Registry with Scopes
 * 
 * Defines tools with read/write scopes and resource constraints.
 * Each tool declares what it can access and what permissions it needs.
 */

interface ToolDefinition {
    scope: "read" | "write";
    resource_constraint?: "path_prefix" | "project_id" | "none";
    allowed_prefixes?: string[];
    allowed_projects?: string[];
    requires_approval?: boolean;
    trust_level: "safe" | "moderate" | "dangerous";
}

export const TOOL_REGISTRY: Record<string, ToolDefinition> = {
    // Read operations - safe
    "repo.read": {
        scope: "read",
        resource_constraint: "path_prefix",
        allowed_prefixes: ["/src", "/docs"],
        trust_level: "safe",
    },
    "docs.search": {
        scope: "read",
        resource_constraint: "none",
        trust_level: "safe",
    },
    "ticket.list": {
        scope: "read",
        resource_constraint: "project_id",
        allowed_projects: ["proj-123", "proj-456"],
        trust_level: "safe",
    },

    // Write operations - moderate
    "ticket.create": {
        scope: "write",
        resource_constraint: "project_id",
        allowed_projects: ["proj-123", "proj-456"],
        trust_level: "moderate",
    },
    "ticket.update": {
        scope: "write",
        resource_constraint: "project_id",
        allowed_projects: ["proj-123", "proj-456"],
        trust_level: "moderate",
    },

    // Write operations - dangerous
    "repo.write": {
        scope: "write",
        resource_constraint: "path_prefix",
        allowed_prefixes: ["/src"],
        requires_approval: true,
        trust_level: "dangerous",
    },
    "repo.delete": {
        scope: "write",
        resource_constraint: "path_prefix",
        allowed_prefixes: ["/src"],
        requires_approval: true,
        trust_level: "dangerous",
    },
    "admin.delete_user": {
        scope: "write",
        resource_constraint: "none",
        requires_approval: true,
        trust_level: "dangerous",
    },
};

export const TOOL_TRUST_LEVELS = {
    safe: ["repo.read", "docs.search", "ticket.list"],
    moderate: ["ticket.create", "ticket.update"],
    dangerous: ["repo.write", "repo.delete", "admin.delete_user"],
};

export function getToolDefinition(toolName: string): ToolDefinition | undefined {
    return TOOL_REGISTRY[toolName];
}

export function requiresApproval(toolName: string): boolean {
    const tool = TOOL_REGISTRY[toolName];
    return tool?.requires_approval === true;
}

export function isToolAllowed(toolName: string, resource: string): boolean {
    const tool = TOOL_REGISTRY[toolName];
    if (!tool) return false;

    if (tool.resource_constraint === "path_prefix" && tool.allowed_prefixes) {
        return tool.allowed_prefixes.some((prefix) => resource.startsWith(prefix));
    }

    if (tool.resource_constraint === "project_id" && tool.allowed_projects) {
        return tool.allowed_projects.includes(resource);
    }

    return true;
}

// Example usage
if (require.main === module) {
    console.log("=== Tool Registry Example ===\n");

    console.log("1. Safe tools (read-only):");
    TOOL_TRUST_LEVELS.safe.forEach((tool) => {
        const def = TOOL_REGISTRY[tool];
        console.log(`   ${tool}: scope=${def.scope}, constraint=${def.resource_constraint}`);
    });

    console.log("\n2. Moderate tools (reversible writes):");
    TOOL_TRUST_LEVELS.moderate.forEach((tool) => {
        const def = TOOL_REGISTRY[tool];
        console.log(`   ${tool}: scope=${def.scope}, constraint=${def.resource_constraint}`);
    });

    console.log("\n3. Dangerous tools (requires approval):");
    TOOL_TRUST_LEVELS.dangerous.forEach((tool) => {
        const def = TOOL_REGISTRY[tool];
        console.log(
            `   ${tool}: scope=${def.scope}, approval=${def.requires_approval}`
        );
    });

    console.log("\n4. Resource constraint checks:");
    console.log(`   repo.read("/src/main.ts"): ${isToolAllowed("repo.read", "/src/main.ts")}`);
    console.log(`   repo.read("/etc/passwd"): ${isToolAllowed("repo.read", "/etc/passwd")}`);
    console.log(`   repo.write("/src/config.ts"): ${isToolAllowed("repo.write", "/src/config.ts")}`);
    console.log(`   repo.write("/docs/readme.md"): ${isToolAllowed("repo.write", "/docs/readme.md")}`);
}
