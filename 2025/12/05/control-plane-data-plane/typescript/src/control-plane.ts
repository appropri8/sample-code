import express, { Request, Response } from 'express';
import axios from 'axios';
import {
  RateLimitPolicy,
  CreateRateLimitPolicyRequest,
  UpdateRateLimitPolicyRequest,
  RollbackRequest,
  AuditEntry,
} from './types';

export class ControlPlaneAPI {
  private policies: Map<string, RateLimitPolicy> = new Map();
  private versions: Map<string, RateLimitPolicy[]> = new Map();
  private auditLog: AuditEntry[] = [];
  private dataPlaneURLs: string[];

  constructor(dataPlaneURLs: string[] = ['http://localhost:3001']) {
    this.dataPlaneURLs = dataPlaneURLs;
    this.startReconciliation();
  }

  createPolicy(req: Request, res: Response) {
    const body: CreateRateLimitPolicyRequest = req.body;

    // Validate
    if (body.limit <= 0 || body.window <= 0) {
      return res.status(400).json({ error: 'limit and window must be positive' });
    }

    // Create policy
    const policy: RateLimitPolicy = {
      id: this.generateID(),
      version: 1,
      tenantId: body.tenantId,
      limit: body.limit,
      window: body.window,
      createdAt: new Date(),
      updatedAt: new Date(),
    };

    this.policies.set(policy.id, policy);
    this.versions.set(policy.id, [policy]);

    // Audit log
    this.logAudit(
      'CREATE_RATE_LIMIT_POLICY',
      policy.id,
      body.userId,
      `limit=${body.limit}, window=${body.window}`
    );

    // Push to data plane (async)
    this.pushToDataPlane(policy).catch((err) =>
      console.error('Failed to push to data plane:', err)
    );

    res.json(policy);
  }

  getPolicy(req: Request, res: Response) {
    const { id } = req.params;
    const version = req.query.version as string | undefined;

    if (version) {
      // Get specific version
      const versions = this.versions.get(id) || [];
      const policy = versions.find((v) => v.version.toString() === version);
      if (!policy) {
        return res.status(404).json({ error: 'version not found' });
      }
      return res.json(policy);
    }

    // Get latest
    const policy = this.policies.get(id);
    if (!policy) {
      return res.status(404).json({ error: 'policy not found' });
    }

    res.json(policy);
  }

  updatePolicy(req: Request, res: Response) {
    const { id } = req.params;
    const body: UpdateRateLimitPolicyRequest = req.body;

    const policy = this.policies.get(id);
    if (!policy) {
      return res.status(404).json({ error: 'policy not found' });
    }

    // Create new version
    const newPolicy: RateLimitPolicy = {
      ...policy,
      version: policy.version + 1,
      updatedAt: new Date(),
    };

    if (body.limit !== undefined) {
      newPolicy.limit = body.limit;
    }
    if (body.window !== undefined) {
      newPolicy.window = body.window;
    }

    this.policies.set(id, newPolicy);
    const versions = this.versions.get(id) || [];
    versions.push(newPolicy);
    this.versions.set(id, versions);

    // Audit log
    this.logAudit('UPDATE_RATE_LIMIT_POLICY', id, body.userId, `version=${newPolicy.version}`);

    // Push to data plane (async)
    this.pushToDataPlane(newPolicy).catch((err) =>
      console.error('Failed to push to data plane:', err)
    );

    res.json(newPolicy);
  }

  rollbackPolicy(req: Request, res: Response) {
    const { id } = req.params;
    const body: RollbackRequest = req.body;

    const versions = this.versions.get(id) || [];
    const targetPolicy = versions.find((v) => v.version === body.targetVersion);

    if (!targetPolicy) {
      return res.status(404).json({ error: 'version not found' });
    }

    // Create new version pointing to old config
    const rolledBack: RateLimitPolicy = {
      ...targetPolicy,
      version: (this.policies.get(id)?.version || 0) + 1,
      updatedAt: new Date(),
    };

    this.policies.set(id, rolledBack);
    versions.push(rolledBack);
    this.versions.set(id, versions);

    // Audit log
    this.logAudit(
      'ROLLBACK_RATE_LIMIT_POLICY',
      id,
      body.userId,
      `to version ${body.targetVersion}: ${body.reason}`
    );

    // Push to data plane (async)
    this.pushToDataPlane(rolledBack).catch((err) =>
      console.error('Failed to push to data plane:', err)
    );

    res.json(rolledBack);
  }

  listPolicies(req: Request, res: Response) {
    const policies = Array.from(this.policies.values());
    res.json(policies);
  }

  getAuditLog(req: Request, res: Response) {
    res.json(this.auditLog);
  }

  health(req: Request, res: Response) {
    res.json({
      status: 'healthy',
      policies: this.policies.size,
    });
  }

  private async pushToDataPlane(policy: RateLimitPolicy): Promise<void> {
    const promises = this.dataPlaneURLs.map((url) =>
      axios.post(`${url}/internal/config/rate-limits`, policy).catch((err) => {
        console.error(`Failed to push to ${url}:`, err.message);
      })
    );
    await Promise.all(promises);
  }

  private startReconciliation() {
    setInterval(() => {
      this.reconcile();
    }, 30000); // Every 30 seconds
  }

  private async reconcile() {
    const policies = Array.from(this.policies.values());
    for (const policy of policies) {
      await this.pushToDataPlane(policy);
    }
  }

  private logAudit(action: string, resourceId: string, userId: string, changes: string) {
    this.auditLog.push({
      action,
      resourceId,
      userId,
      changes,
      timestamp: new Date(),
    });
  }

  private generateID(): string {
    return `policy-${Date.now()}`;
  }
}

// Server setup
const app = express();
app.use(express.json());

const controlPlane = new ControlPlaneAPI();

app.post('/api/v1/rate-limit-policies', (req, res) => controlPlane.createPolicy(req, res));
app.get('/api/v1/rate-limit-policies/:id', (req, res) => controlPlane.getPolicy(req, res));
app.put('/api/v1/rate-limit-policies/:id', (req, res) => controlPlane.updatePolicy(req, res));
app.post('/api/v1/rate-limit-policies/:id/rollback', (req, res) =>
  controlPlane.rollbackPolicy(req, res)
);
app.get('/api/v1/rate-limit-policies', (req, res) => controlPlane.listPolicies(req, res));
app.get('/api/v1/audit', (req, res) => controlPlane.getAuditLog(req, res));
app.get('/health', (req, res) => controlPlane.health(req, res));

const port = process.env.PORT || 3000;
app.listen(port, () => {
  console.log(`Control plane running on port ${port}`);
});
