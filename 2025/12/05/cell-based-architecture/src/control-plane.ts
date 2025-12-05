import express, { Request, Response } from 'express';
import { Cell, Tenant, RoutingRule, TenantMapping } from './types';

export class ControlPlane {
  private cells: Map<string, Cell> = new Map();
  private tenants: Map<string, Tenant> = new Map();
  private routingRules: Map<string, RoutingRule> = new Map();
  private app: express.Application;
  private routingVersion: number = 1;

  constructor() {
    this.app = express();
    this.app.use(express.json());
    this.setupRoutes();
    this.initializeSampleData();
  }

  private setupRoutes(): void {
    // Health check
    this.app.get('/health', (req: Request, res: Response) => {
      res.json({ status: 'healthy' });
    });

    // Get routing table
    this.app.get('/api/routing/tenants', (req: Request, res: Response) => {
      const mappings: TenantMapping[] = [];
      
      for (const tenant of this.tenants.values()) {
        mappings.push({
          tenantId: tenant.id,
          cellId: tenant.cellId,
        });
      }

      res.json({
        mappings,
        version: this.routingVersion,
        updatedAt: new Date().toISOString(),
      });
    });

    // Get cell by ID
    this.app.get('/api/cells/:cellId', (req: Request, res: Response) => {
      const cell = this.cells.get(req.params.cellId);
      if (!cell) {
        return res.status(404).json({ error: 'Cell not found' });
      }
      res.json(cell);
    });

    // List all cells
    this.app.get('/api/cells', (req: Request, res: Response) => {
      const cells = Array.from(this.cells.values());
      res.json({ cells });
    });

    // Get tenant by ID
    this.app.get('/api/tenants/:tenantId', (req: Request, res: Response) => {
      const tenant = this.tenants.get(req.params.tenantId);
      if (!tenant) {
        return res.status(404).json({ error: 'Tenant not found' });
      }
      res.json(tenant);
    });

    // Create tenant
    this.app.post('/api/tenants', (req: Request, res: Response) => {
      const tenant: Tenant = {
        id: req.body.id,
        cellId: req.body.cellId,
        name: req.body.name,
        tier: req.body.tier || 'free',
        region: req.body.region,
        migratedAt: new Date(),
      };

      this.tenants.set(tenant.id, tenant);
      this.routingVersion++;
      
      res.status(201).json(tenant);
    });

    // Move tenant to different cell
    this.app.post('/api/tenants/:tenantId/migrate', (req: Request, res: Response) => {
      const tenant = this.tenants.get(req.params.tenantId);
      if (!tenant) {
        return res.status(404).json({ error: 'Tenant not found' });
      }

      const newCellId = req.body.cellId;
      if (!this.cells.has(newCellId)) {
        return res.status(400).json({ error: 'Target cell not found' });
      }

      tenant.cellId = newCellId;
      tenant.migratedAt = new Date();
      this.routingVersion++;

      res.json(tenant);
    });

    // Create cell
    this.app.post('/api/cells', (req: Request, res: Response) => {
      const cell: Cell = {
        id: req.body.id,
        region: req.body.region,
        status: req.body.status || 'active',
        capacity: {
          maxTenants: req.body.capacity?.maxTenants || 100,
          currentTenants: 0,
        },
        endpoints: {
          api: req.body.endpoints?.api || `https://api-${req.body.id}.example.com`,
          metrics: req.body.endpoints?.metrics || `https://metrics-${req.body.id}.example.com`,
        },
        createdAt: new Date(),
        updatedAt: new Date(),
      };

      this.cells.set(cell.id, cell);
      res.status(201).json(cell);
    });
  }

  private initializeSampleData(): void {
    // Create sample cells
    this.cells.set('cell-us-east-1', {
      id: 'cell-us-east-1',
      region: 'us-east-1',
      status: 'active',
      capacity: {
        maxTenants: 100,
        currentTenants: 2,
      },
      endpoints: {
        api: 'https://api-cell-us-east-1.example.com',
        metrics: 'https://metrics-cell-us-east-1.example.com',
      },
      createdAt: new Date('2025-12-01'),
      updatedAt: new Date('2025-12-01'),
    });

    this.cells.set('cell-eu-west-1', {
      id: 'cell-eu-west-1',
      region: 'eu-west-1',
      status: 'active',
      capacity: {
        maxTenants: 100,
        currentTenants: 1,
      },
      endpoints: {
        api: 'https://api-cell-eu-west-1.example.com',
        metrics: 'https://metrics-cell-eu-west-1.example.com',
      },
      createdAt: new Date('2025-12-01'),
      updatedAt: new Date('2025-12-01'),
    });

    // Create sample tenants
    this.tenants.set('tenant-acme', {
      id: 'tenant-acme',
      cellId: 'cell-us-east-1',
      name: 'Acme Corporation',
      tier: 'enterprise',
      region: 'us-east-1',
      migratedAt: new Date('2025-12-01'),
    });

    this.tenants.set('tenant-beta', {
      id: 'tenant-beta',
      cellId: 'cell-us-east-1',
      name: 'Beta Corp',
      tier: 'paid',
      region: 'us-east-1',
      migratedAt: new Date('2025-12-01'),
    });

    this.tenants.set('tenant-eu-corp', {
      id: 'tenant-eu-corp',
      cellId: 'cell-eu-west-1',
      name: 'EU Corporation',
      tier: 'enterprise',
      region: 'eu-west-1',
      migratedAt: new Date('2025-12-01'),
    });
  }

  start(port: number = 3001): void {
    this.app.listen(port, () => {
      console.log(`Control plane API running on port ${port}`);
      console.log(`Health check: http://localhost:${port}/health`);
      console.log(`Routing API: http://localhost:${port}/api/routing/tenants`);
    });
  }

  getApp(): express.Application {
    return this.app;
  }
}
