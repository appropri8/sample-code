/**
 * Core types for multi-tenant SaaS system.
 */

export interface TenantContext {
  tenantId: string;
  tier: 'free' | 'standard' | 'enterprise';
  features: string[];
  rateLimitPerMinute: number;
  quotaLimits: {
    requestsPerMinute: number;
    jobsPerMinute: number;
    storageBytes: number;
    queryCostPerMonth: number;
  };
}

export interface Tenant {
  id: string;
  name: string;
  tier: 'free' | 'standard' | 'enterprise';
  subdomain?: string;
  apiKey?: string;
  createdAt: Date;
}

export interface User {
  id: string;
  tenantId: string;
  email: string;
  name: string;
  createdAt: Date;
}

export interface Order {
  id: string;
  tenantId: string;
  userId: string;
  amount: number;
  status: 'pending' | 'completed' | 'cancelled';
  createdAt: Date;
}

