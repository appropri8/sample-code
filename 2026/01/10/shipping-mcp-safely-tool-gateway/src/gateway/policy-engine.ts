import type {
  Policy,
  PolicyDecision,
  ToolCallContext,
  RateLimit,
} from '../types';

/**
 * In-memory policy store.
 * In production, load from YAML/JSON config file or database.
 */
const policies = new Map<string, Policy>();

/**
 * Rate limit tracking (in-memory, use Redis in production)
 */
const rateLimitCounters = new Map<
  string,
  { count: number; resetAt: number }
>();

/**
 * Load a policy into the store
 */
export function loadPolicy(policy: Policy): void {
  policies.set(policy.tool, policy);
}

/**
 * Load multiple policies
 */
export function loadPolicies(policyList: Policy[]): void {
  for (const policy of policyList) {
    loadPolicy(policy);
  }
}

/**
 * Evaluate policy for a tool call
 */
export async function evaluatePolicy(
  tool: string,
  context: ToolCallContext
): Promise<PolicyDecision> {
  const policy = policies.get(tool);
  
  if (!policy) {
    return {
      decision: 'deny',
      reason: `Tool not found: ${tool}`,
    };
  }

  // Check role
  const userRole = context.userRole || 'default';
  if (!policy.allowedRoles.includes(userRole)) {
    return {
      decision: 'deny',
      reason: `Role '${userRole}' not allowed for tool '${tool}'. Allowed roles: ${policy.allowedRoles.join(', ')}`,
    };
  }

  // Check workspace if specified
  if (
    policy.allowedWorkspaces &&
    !policy.allowedWorkspaces.includes(context.workspaceId)
  ) {
    return {
      decision: 'deny',
      reason: `Workspace '${context.workspaceId}' not allowed for tool '${tool}'`,
    };
  }

  // Check rate limit
  if (policy.constraints.rateLimit) {
    const rateLimitCheck = await checkRateLimit(
      context.userId,
      context.workspaceId,
      policy.constraints.rateLimit
    );
    if (!rateLimitCheck.allowed) {
      return {
        decision: 'deny',
        reason: `Rate limit exceeded: ${rateLimitCheck.reason}`,
      };
    }
  }

  // Check if elevation is required
  if (policy.requiresElevation) {
    // In production, check for valid elevation token
    // For now, we'll allow but log that elevation should be checked
    console.warn(
      `[POLICY] Tool ${tool} requires elevation, but elevation check not implemented`
    );
  }

  return {
    decision: 'allow',
    sandboxConfig: policy.sandbox,
  };
}

/**
 * Check rate limit for user and workspace
 */
async function checkRateLimit(
  userId: string,
  workspaceId: string,
  rateLimit: RateLimit
): Promise<{ allowed: boolean; reason?: string }> {
  const now = Date.now();

  // Check user rate limit
  const userKey = `user:${userId}`;
  const userCounter = rateLimitCounters.get(userKey);
  
  if (userCounter) {
    if (now < userCounter.resetAt) {
      if (userCounter.count >= rateLimit.perUser.requests) {
        return {
          allowed: false,
          reason: `User rate limit exceeded: ${userCounter.count}/${rateLimit.perUser.requests}`,
        };
      }
      userCounter.count++;
    } else {
      // Reset counter
      rateLimitCounters.set(userKey, {
        count: 1,
        resetAt: now + rateLimit.perUser.window,
      });
    }
  } else {
    rateLimitCounters.set(userKey, {
      count: 1,
      resetAt: now + rateLimit.perUser.window,
    });
  }

  // Check workspace rate limit if specified
  if (rateLimit.perWorkspace) {
    const workspaceKey = `workspace:${workspaceId}`;
    const workspaceCounter = rateLimitCounters.get(workspaceKey);
    
    if (workspaceCounter) {
      if (now < workspaceCounter.resetAt) {
        if (workspaceCounter.count >= rateLimit.perWorkspace.requests) {
          return {
            allowed: false,
            reason: `Workspace rate limit exceeded: ${workspaceCounter.count}/${rateLimit.perWorkspace.requests}`,
          };
        }
        workspaceCounter.count++;
      } else {
        rateLimitCounters.set(workspaceKey, {
          count: 1,
          resetAt: now + rateLimit.perWorkspace.window,
        });
      }
    } else {
      rateLimitCounters.set(workspaceKey, {
        count: 1,
        resetAt: now + rateLimit.perWorkspace.window,
      });
    }
  }

  return { allowed: true };
}

/**
 * Get policy for a tool (for testing)
 */
export function getPolicy(tool: string): Policy | undefined {
  return policies.get(tool);
}

/**
 * Clear all policies (for testing)
 */
export function clearPolicies(): void {
  policies.clear();
  rateLimitCounters.clear();
}
