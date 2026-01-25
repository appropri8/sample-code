export interface ToolCallRequest {
  tool: string;
  arguments: Record<string, unknown>;
  context: ToolCallContext;
}

export interface ToolCallContext {
  userId: string;
  workspaceId: string;
  sessionId: string;
  userRole?: string;
  source?: 'trusted' | 'web' | 'email' | 'upload';
}

export interface ToolCallResponse {
  success: boolean;
  result?: unknown;
  error?: string;
  auditId: string;
}

export interface Policy {
  tool: string;
  allowedRoles: string[];
  allowedWorkspaces?: string[];
  requiresElevation?: boolean;
  constraints: PolicyConstraints;
  sandbox?: SandboxConfig;
}

export interface PolicyConstraints {
  maxArguments?: number;
  requiredFields?: string[];
  pathConstraints?: PathConstraint[];
  rateLimit?: RateLimit;
  allowedCommands?: string[];
  maxFileSize?: number;
}

export interface PathConstraint {
  type: 'allow' | 'deny';
  pattern: string;
  basePath: string;
}

export interface RateLimit {
  perUser: {
    requests: number;
    window: number; // milliseconds
  };
  perWorkspace?: {
    requests: number;
    window: number;
  };
}

export interface SandboxConfig {
  type: 'container' | 'vm';
  networkPolicy: 'deny' | 'allow-list';
  allowedHosts?: string[];
  timeout: number;
  memoryLimit: string;
  cpuLimit: string;
}

export interface PolicyDecision {
  decision: 'allow' | 'deny';
  reason?: string;
  sandboxConfig?: SandboxConfig;
}

export interface ValidationResult {
  valid: boolean;
  errors?: string[];
}

export interface AuditLog {
  auditId: string;
  timestamp: string;
  userId: string;
  workspaceId: string;
  tool: string;
  arguments: Record<string, unknown>;
  policyDecision: 'allow' | 'deny';
  executionResult: 'success' | 'error' | 'timeout';
  duration: number;
  sandboxId?: string;
  error?: string;
}

export interface ExecutionResult {
  success: boolean;
  output?: string;
  exitCode?: number;
  error?: string;
}
