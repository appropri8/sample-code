/**
 * Per-tenant quota management.
 * 
 * This module demonstrates how to enforce quotas per tenant
 * for different resources: requests, jobs, storage, query cost.
 */

import { TenantContext } from './types';

/**
 * Quota limits for a resource.
 */
interface QuotaLimit {
  max: number;
  window: 'minute' | 'hour' | 'day' | 'month';
}

/**
 * Quota manager that tracks usage per tenant per resource.
 */
export class TenantQuotaManager {
  private usage = new Map<string, Map<string, { count: number; resetAt: number }>>();
  
  /**
   * Check if tenant has quota available for resource.
   */
  async checkQuota(
    tenantId: string,
    resource: string,
    limit: QuotaLimit
  ): Promise<{ allowed: boolean; remaining: number; resetAt: number }> {
    const key = `${tenantId}:${resource}`;
    const now = Date.now();
    const windowMs = this.getWindowMs(limit.window);
    const resetAt = now + windowMs;
    
    let usage = this.usage.get(key);
    
    if (!usage || now > usage.resetAt) {
      // New window
      usage = { count: 0, resetAt };
      this.usage.set(key, usage);
    }
    
    const remaining = Math.max(0, limit.max - usage.count);
    const allowed = usage.count < limit.max;
    
    return { allowed, remaining, resetAt: usage.resetAt };
  }
  
  /**
   * Consume quota for tenant and resource.
   */
  async consumeQuota(
    tenantId: string,
    resource: string,
    limit: QuotaLimit,
    amount: number = 1
  ): Promise<{ allowed: boolean; remaining: number }> {
    const check = await this.checkQuota(tenantId, resource, limit);
    
    if (!check.allowed) {
      return { allowed: false, remaining: check.remaining };
    }
    
    const key = `${tenantId}:${resource}`;
    const usage = this.usage.get(key)!;
    usage.count += amount;
    
    return {
      allowed: true,
      remaining: Math.max(0, limit.max - usage.count)
    };
  }
  
  private getWindowMs(window: string): number {
    switch (window) {
      case 'minute': return 60000;
      case 'hour': return 3600000;
      case 'day': return 86400000;
      case 'month': return 2592000000; // 30 days
      default: return 60000;
    }
  }
}

/**
 * Quota manager that uses tenant context to determine limits.
 */
export class TenantAwareQuotaManager {
  private manager: TenantQuotaManager;
  
  constructor() {
    this.manager = new TenantQuotaManager();
  }
  
  /**
   * Check requests per minute quota.
   */
  async checkRequestsQuota(tenant: TenantContext): Promise<{
    allowed: boolean;
    remaining: number;
    resetAt: number;
  }> {
    return this.manager.checkQuota(
      tenant.tenantId,
      'requests',
      {
        max: tenant.quotaLimits.requestsPerMinute,
        window: 'minute'
      }
    );
  }
  
  /**
   * Check jobs per minute quota.
   */
  async checkJobsQuota(tenant: TenantContext): Promise<{
    allowed: boolean;
    remaining: number;
    resetAt: number;
  }> {
    return this.manager.checkQuota(
      tenant.tenantId,
      'jobs',
      {
        max: tenant.quotaLimits.jobsPerMinute,
        window: 'minute'
      }
    );
  }
  
  /**
   * Check storage quota.
   */
  async checkStorageQuota(
    tenant: TenantContext,
    currentUsage: number,
    requestedSize: number
  ): Promise<{
    allowed: boolean;
    remaining: number;
  }> {
    const total = currentUsage + requestedSize;
    const allowed = total <= tenant.quotaLimits.storageBytes;
    const remaining = Math.max(0, tenant.quotaLimits.storageBytes - total);
    
    return { allowed, remaining };
  }
  
  /**
   * Check query cost quota.
   */
  async checkQueryCostQuota(
    tenant: TenantContext,
    currentCost: number,
    estimatedCost: number
  ): Promise<{
    allowed: boolean;
    remaining: number;
  }> {
    const total = currentCost + estimatedCost;
    const allowed = total <= tenant.quotaLimits.queryCostPerMonth;
    const remaining = Math.max(0, tenant.quotaLimits.queryCostPerMonth - total);
    
    return { allowed, remaining };
  }
}

/**
 * Handle quota exceeded gracefully for individual tenant.
 */
export function handleQuotaExceeded(
  tenant: TenantContext,
  resource: string,
  retryAfter: number
): {
  status: number;
  body: {
    error: string;
    resource: string;
    retryAfter: number;
    upgradeMessage?: string;
  };
} {
  const upgradeMessage = tenant.tier === 'free'
    ? 'Upgrade to increase quota'
    : tenant.tier === 'standard'
    ? 'Upgrade to enterprise for higher limits'
    : 'Contact support';
  
  return {
    status: 429,
    body: {
      error: 'Quota exceeded',
      resource,
      retryAfter,
      upgradeMessage
    }
  };
}

