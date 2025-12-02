/**
 * Tenant context propagation and management.
 * 
 * This module handles extracting tenant ID from requests and
 * creating tenant context objects that flow through the system.
 */

import { Request, Response, NextFunction } from 'express';
import { TenantContext, Tenant } from './types';

/**
 * Extended request type with tenant context.
 */
export interface RequestWithTenant extends Request {
  tenant: TenantContext;
}

/**
 * Extract tenant ID from various sources.
 */
export function extractTenantId(req: Request): string | null {
  // Option 1: From JWT token (after authentication)
  const authHeader = req.headers.authorization;
  if (authHeader) {
    // In real implementation, verify JWT and extract tenant_id
    // const token = jwt.verify(authHeader.replace('Bearer ', ''));
    // return token.tenantId;
  }
  
  // Option 2: From API key header
  const apiKey = req.headers['x-api-key'] as string;
  if (apiKey) {
    // In real implementation, lookup tenant by API key
    // const tenant = await getTenantByApiKey(apiKey);
    // return tenant?.id;
  }
  
  // Option 3: From subdomain
  const hostname = req.hostname;
  const subdomain = hostname.split('.')[0];
  if (subdomain && subdomain !== 'www' && subdomain !== 'api') {
    // In real implementation, lookup tenant by subdomain
    // const tenant = await getTenantBySubdomain(subdomain);
    // return tenant?.id;
  }
  
  // Option 4: From header
  const tenantIdHeader = req.headers['x-tenant-id'] as string;
  if (tenantIdHeader) {
    return tenantIdHeader;
  }
  
  // Option 5: From path parameter
  const tenantIdParam = req.params.tenantId;
  if (tenantIdParam) {
    return tenantIdParam;
  }
  
  return null;
}

/**
 * Get tenant context from tenant ID.
 * In real implementation, this would fetch from database.
 */
async function getTenantContext(tenantId: string): Promise<TenantContext | null> {
  // Mock implementation - in real system, fetch from database
  const mockTenants: Record<string, TenantContext> = {
    'tenant-1': {
      tenantId: 'tenant-1',
      tier: 'enterprise',
      features: ['feature-a', 'feature-b'],
      rateLimitPerMinute: 10000,
      quotaLimits: {
        requestsPerMinute: 10000,
        jobsPerMinute: 1000,
        storageBytes: 1000000000, // 1GB
        queryCostPerMonth: 1000
      }
    },
    'tenant-2': {
      tenantId: 'tenant-2',
      tier: 'standard',
      features: ['feature-a'],
      rateLimitPerMinute: 1000,
      quotaLimits: {
        requestsPerMinute: 1000,
        jobsPerMinute: 100,
        storageBytes: 100000000, // 100MB
        queryCostPerMonth: 100
      }
    },
    'tenant-3': {
      tenantId: 'tenant-3',
      tier: 'free',
      features: [],
      rateLimitPerMinute: 100,
      quotaLimits: {
        requestsPerMinute: 100,
        jobsPerMinute: 10,
        storageBytes: 10000000, // 10MB
        queryCostPerMonth: 10
      }
    }
  };
  
  return mockTenants[tenantId] || null;
}

/**
 * Middleware that extracts tenant ID and attaches tenant context to request.
 * Refuses to proceed if tenant ID is missing or invalid.
 */
export function tenantMiddleware(
  req: RequestWithTenant,
  res: Response,
  next: NextFunction
): void {
  const tenantId = extractTenantId(req);
  
  if (!tenantId) {
    res.status(401).json({ 
      error: 'Tenant ID required',
      message: 'Provide tenant ID via X-Tenant-Id header, subdomain, or API key'
    });
    return;
  }
  
  // In real implementation, this would be async
  getTenantContext(tenantId).then(tenant => {
    if (!tenant) {
      res.status(404).json({ 
        error: 'Tenant not found',
        tenantId 
      });
      return;
    }
    
    req.tenant = tenant;
    next();
  }).catch(err => {
    res.status(500).json({ 
      error: 'Failed to load tenant context',
      message: err.message 
    });
  });
}

/**
 * Require tenant context - throws if missing.
 * Use this in handlers to ensure tenant context exists.
 */
export function requireTenant(req: RequestWithTenant): TenantContext {
  if (!req.tenant) {
    throw new Error('Tenant context required');
  }
  return req.tenant;
}

/**
 * Validate that a user belongs to a tenant.
 */
export async function validateTenantAccess(
  userId: string,
  tenantId: string
): Promise<boolean> {
  // In real implementation, check database
  // const user = await getUser(userId);
  // return user.tenantId === tenantId;
  
  // Mock implementation
  return true;
}

