export interface RateLimitPolicy {
  id: string;
  version: number;
  tenantId: string;
  limit: number;
  window: number; // seconds
  createdAt: Date;
  updatedAt: Date;
}

export interface AuditEntry {
  action: string;
  resourceId: string;
  userId: string;
  changes: string;
  timestamp: Date;
}

export interface CreateRateLimitPolicyRequest {
  tenantId: string;
  limit: number;
  window: number;
  userId: string;
}

export interface UpdateRateLimitPolicyRequest {
  limit?: number;
  window?: number;
  userId: string;
}

export interface RollbackRequest {
  targetVersion: number;
  reason: string;
  userId: string;
}
