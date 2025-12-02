/**
 * Main entry point demonstrating multi-tenant SaaS with strong isolation.
 * 
 * This server shows:
 * - Tenant context extraction and propagation
 * - Tenant-aware repositories
 * - Per-tenant rate limiting
 * - Per-tenant quota management
 */

import express, { Request, Response } from 'express';
import { Pool } from 'pg';
import Redis from 'ioredis';
import {
  tenantMiddleware,
  requireTenant,
  RequestWithTenant
} from './tenant-context';
import { OrderRepository, RepositoryFactory } from './tenant-repository';
import { TenantAwareRateLimiter } from './rate-limiter';
import { TenantAwareQuotaManager, handleQuotaExceeded } from './quota-manager';

const app = express();
app.use(express.json());

// Database connection (in real implementation, use connection pooling)
const db = new Pool({
  host: process.env.DB_HOST || 'localhost',
  port: parseInt(process.env.DB_PORT || '5432'),
  database: process.env.DB_NAME || 'saas_db',
  user: process.env.DB_USER || 'postgres',
  password: process.env.DB_PASSWORD || 'postgres'
});

// Redis connection for rate limiting
const redis = new Redis({
  host: process.env.REDIS_HOST || 'localhost',
  port: parseInt(process.env.REDIS_PORT || '6379')
});

// Initialize services
const repositoryFactory = new RepositoryFactory(db);
const rateLimiter = new TenantAwareRateLimiter(redis);
const quotaManager = new TenantAwareQuotaManager();

/**
 * Health check endpoint.
 */
app.get('/health', (req: Request, res: Response) => {
  res.json({ status: 'ok' });
});

/**
 * Get orders for tenant.
 * Demonstrates:
 * - Tenant context extraction
 * - Tenant-aware repository
 * - Rate limiting
 * - Quota checking
 */
app.get(
  '/api/orders',
  tenantMiddleware,
  async (req: RequestWithTenant, res: Response) => {
    try {
      const tenant = requireTenant(req);
      
      // Check rate limit
      const rateLimitInfo = await rateLimiter.getRateLimitInfo(tenant);
      if (!rateLimitInfo.allowed) {
        return res.status(429)
          .setHeader('Retry-After', rateLimitInfo.resetIn.toString())
          .json({
            error: 'Rate limit exceeded',
            retryAfter: rateLimitInfo.resetIn,
            limit: rateLimitInfo.limit
          });
      }
      
      // Check quota
      const quotaCheck = await quotaManager.checkRequestsQuota(tenant);
      if (!quotaCheck.allowed) {
        const response = handleQuotaExceeded(
          tenant,
          'requests',
          Math.ceil((quotaCheck.resetAt - Date.now()) / 1000)
        );
        return res.status(response.status).json(response.body);
      }
      
      // Consume quota
      await quotaManager.consumeQuota(
        tenant.tenantId,
        'requests',
        { max: tenant.quotaLimits.requestsPerMinute, window: 'minute' },
        1
      );
      
      // Get orders using tenant-aware repository
      const orderRepo = repositoryFactory.createOrderRepository(tenant.tenantId);
      const orders = await orderRepo.findAll();
      
      res.json({
        orders,
        rateLimit: {
          remaining: rateLimitInfo.remaining,
          resetIn: rateLimitInfo.resetIn,
          limit: rateLimitInfo.limit
        },
        quota: {
          remaining: quotaCheck.remaining,
          resetAt: new Date(quotaCheck.resetAt).toISOString()
        }
      });
    } catch (error: any) {
      console.error('Error getting orders:', error);
      res.status(500).json({ error: 'Internal server error' });
    }
  }
);

/**
 * Get order by ID for tenant.
 */
app.get(
  '/api/orders/:orderId',
  tenantMiddleware,
  async (req: RequestWithTenant, res: Response) => {
    try {
      const tenant = requireTenant(req);
      const { orderId } = req.params;
      
      const orderRepo = repositoryFactory.createOrderRepository(tenant.tenantId);
      const order = await orderRepo.findById(orderId);
      
      if (!order) {
        return res.status(404).json({ error: 'Order not found' });
      }
      
      res.json(order);
    } catch (error: any) {
      console.error('Error getting order:', error);
      res.status(500).json({ error: 'Internal server error' });
    }
  }
);

/**
 * Create order for tenant.
 */
app.post(
  '/api/orders',
  tenantMiddleware,
  async (req: RequestWithTenant, res: Response) => {
    try {
      const tenant = requireTenant(req);
      const { userId, amount, status } = req.body;
      
      // Check quota
      const quotaCheck = await quotaManager.checkRequestsQuota(tenant);
      if (!quotaCheck.allowed) {
        const response = handleQuotaExceeded(
          tenant,
          'requests',
          Math.ceil((quotaCheck.resetAt - Date.now()) / 1000)
        );
        return res.status(response.status).json(response.body);
      }
      
      // Consume quota
      await quotaManager.consumeQuota(
        tenant.tenantId,
        'requests',
        { max: tenant.quotaLimits.requestsPerMinute, window: 'minute' },
        1
      );
      
      const orderRepo = repositoryFactory.createOrderRepository(tenant.tenantId);
      const order = await orderRepo.create({
        userId,
        amount,
        status: status || 'pending'
      });
      
      res.status(201).json(order);
    } catch (error: any) {
      console.error('Error creating order:', error);
      res.status(500).json({ error: 'Internal server error' });
    }
  }
);

/**
 * Get tenant metrics.
 */
app.get(
  '/api/metrics',
  tenantMiddleware,
  async (req: RequestWithTenant, res: Response) => {
    try {
      const tenant = requireTenant(req);
      
      const rateLimitInfo = await rateLimiter.getRateLimitInfo(tenant);
      const quotaCheck = await quotaManager.checkRequestsQuota(tenant);
      
      res.json({
        tenant: {
          id: tenant.tenantId,
          tier: tenant.tier
        },
        rateLimit: {
          remaining: rateLimitInfo.remaining,
          resetIn: rateLimitInfo.resetIn,
          limit: rateLimitInfo.limit
        },
        quota: {
          requests: {
            remaining: quotaCheck.remaining,
            limit: tenant.quotaLimits.requestsPerMinute,
            resetAt: new Date(quotaCheck.resetAt).toISOString()
          },
          jobs: {
            limit: tenant.quotaLimits.jobsPerMinute
          },
          storage: {
            limit: tenant.quotaLimits.storageBytes
          },
          queryCost: {
            limit: tenant.quotaLimits.queryCostPerMonth
          }
        }
      });
    } catch (error: any) {
      console.error('Error getting metrics:', error);
      res.status(500).json({ error: 'Internal server error' });
    }
  }
);

const PORT = process.env.PORT || 3000;

app.listen(PORT, () => {
  console.log(`Multi-tenant SaaS server running on port ${PORT}`);
  console.log(`Health check: http://localhost:${PORT}/health`);
  console.log(`Get orders: http://localhost:${PORT}/api/orders`);
  console.log(`Headers: X-Tenant-Id: tenant-1 (or tenant-2, tenant-3)`);
});

