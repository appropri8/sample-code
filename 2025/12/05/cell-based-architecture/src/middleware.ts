import { Request, Response, NextFunction } from 'express';
import { CellRouter } from './router';
import { CellContext } from './types';

declare global {
  namespace Express {
    interface Request {
      cellContext?: CellContext;
    }
  }
}

export function cellAwareMiddleware(router: CellRouter) {
  return async (req: Request, res: Response, next: NextFunction) => {
    try {
      // Extract tenant ID from auth token or header
      const tenantId = extractTenantId(req);
      if (!tenantId) {
        return res.status(401).json({ error: 'Missing tenant ID' });
      }

      // Look up cell ID
      const cellId = await router.getCellForTenant(tenantId);
      if (!cellId) {
        return res.status(503).json({ 
          error: 'No cell available for tenant',
          tenantId 
        });
      }

      // Attach cell context to request
      req.cellContext = {
        tenantId,
        cellId,
        region: extractRegion(req),
      };

      // Add cell ID to header for downstream services
      req.headers['x-cell-id'] = cellId;
      req.headers['x-tenant-id'] = tenantId;

      next();
    } catch (error) {
      console.error('Cell routing error:', error);
      res.status(500).json({ error: 'Internal routing error' });
    }
  };
}

function extractTenantId(req: Request): string | null {
  // Try JWT token first
  const authHeader = req.headers.authorization;
  if (authHeader?.startsWith('Bearer ')) {
    const token = authHeader.substring(7);
    const payload = parseJWT(token);
    if (payload?.tenantId) {
      return payload.tenantId;
    }
  }

  // Fallback to header
  return (req.headers['x-tenant-id'] as string) || null;
}

function extractRegion(req: Request): string | undefined {
  return (req.headers['x-region'] as string) || 
         (req.headers['cf-ipcountry'] as string) || 
         undefined;
}

function parseJWT(token: string): any {
  try {
    const parts = token.split('.');
    if (parts.length !== 3) {
      return null;
    }
    const payload = JSON.parse(Buffer.from(parts[1], 'base64').toString());
    return payload;
  } catch {
    return null;
  }
}
