/**
 * Example: Tenant context propagation.
 * 
 * Demonstrates how tenant ID is extracted from requests
 * and flows through the system.
 */

import express, { Request, Response } from 'express';
import {
  tenantMiddleware,
  requireTenant,
  RequestWithTenant
} from '../src/tenant-context';

const app = express();
app.use(express.json());

/**
 * Example endpoint that requires tenant context.
 */
app.get(
  '/api/data',
  tenantMiddleware, // Extracts tenant ID and attaches tenant context
  async (req: RequestWithTenant, res: Response) => {
    // requireTenant ensures tenant context exists (throws if missing)
    const tenant = requireTenant(req);
    
    res.json({
      message: 'Data for tenant',
      tenantId: tenant.tenantId,
      tier: tenant.tier,
      features: tenant.features
    });
  }
);

/**
 * Example: Handler that refuses to run if tenant is missing.
 */
app.get(
  '/api/protected',
  tenantMiddleware,
  async (req: RequestWithTenant, res: Response) => {
    // This will throw if tenant context is missing
    try {
      const tenant = requireTenant(req);
      res.json({ data: 'protected data', tenantId: tenant.tenantId });
    } catch (error: any) {
      res.status(401).json({ error: error.message });
    }
  }
);

const PORT = 3001;

app.listen(PORT, () => {
  console.log(`Tenant context example server running on port ${PORT}`);
  console.log(`Try: curl -H "X-Tenant-Id: tenant-1" http://localhost:${PORT}/api/data`);
});

