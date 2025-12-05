import express, { Request, Response } from 'express';
import axios from 'axios';
import { RateLimitPolicy } from './types';

interface Counter {
  value: number;
  expiresAt: Date;
}

class InMemoryCounterStore {
  private counters: Map<string, Counter> = new Map();

  increment(key: string, ttl: number): number {
    const counter = this.counters.get(key);
    const now = new Date();

    if (!counter || now > counter.expiresAt) {
      const expiresAt = new Date(now.getTime() + ttl * 1000);
      this.counters.set(key, { value: 0, expiresAt });
    }

    const current = this.counters.get(key)!;
    current.value++;
    return current.value;
  }

  get(key: string): number {
    const counter = this.counters.get(key);
    if (!counter || new Date() > counter.expiresAt) {
      return 0;
    }
    return counter.value;
  }
}

class RateLimiter {
  private policies: Map<string, RateLimitPolicy> = new Map();
  private counters: InMemoryCounterStore;
  private defaultLimit = 100;
  private defaultWindow = 60;

  constructor(counters: InMemoryCounterStore) {
    this.counters = counters;
  }

  isAllowed(tenantId: string): boolean {
    const policy = this.policies.get(tenantId);

    // Use default if no policy
    const effectivePolicy = policy || {
      limit: this.defaultLimit,
      window: this.defaultWindow,
    } as RateLimitPolicy;

    // Create counter key based on time window
    const windowStart = Math.floor(Date.now() / 1000 / effectivePolicy.window);
    const key = `${tenantId}:${windowStart}`;

    const count = this.counters.increment(key, effectivePolicy.window);
    return count <= effectivePolicy.limit;
  }

  updatePolicy(policy: RateLimitPolicy): void {
    const existing = this.policies.get(policy.tenantId);
    // Only update if version is newer
    if (!existing || policy.version > existing.version) {
      this.policies.set(policy.tenantId, policy);
      console.log(
        `Policy updated: tenant=${policy.tenantId}, version=${policy.version}, limit=${policy.limit}`
      );
    }
  }

  getPolicy(tenantId: string): RateLimitPolicy | undefined {
    return this.policies.get(tenantId);
  }

  getPolicyCount(): number {
    return this.policies.size;
  }
}

export class DataPlaneAPI {
  private limiter: RateLimiter;
  private controlPlaneURL: string;

  constructor(controlPlaneURL: string = 'http://localhost:3000') {
    const counters = new InMemoryCounterStore();
    this.limiter = new RateLimiter(counters);
    this.controlPlaneURL = controlPlaneURL;
    this.startConfigWatcher();
  }

  handleRequest(req: Request, res: Response) {
    const { tenantId, requestId } = req.body;

    if (!tenantId) {
      return res.status(400).json({ error: 'tenantId required' });
    }

    // Check rate limit
    if (!this.limiter.isAllowed(tenantId)) {
      return res.status(429).json({
        error: 'rate limit exceeded',
        tenantId,
      });
    }

    // Process request
    const policy = this.limiter.getPolicy(tenantId);
    const response: any = {
      status: 'allowed',
      tenantId,
      requestId,
    };

    if (policy) {
      response.limit = policy.limit;
      response.window = policy.window;
    }

    res.json(response);
  }

  updateConfig(req: Request, res: Response) {
    const policy: RateLimitPolicy = req.body;
    this.limiter.updatePolicy(policy);
    res.json({ status: 'updated' });
  }

  health(req: Request, res: Response) {
    res.json({
      status: 'healthy',
      policies: this.limiter.getPolicyCount(),
    });
  }

  metrics(req: Request, res: Response) {
    res.json({
      policies: this.limiter.getPolicyCount(),
      controlPlaneURL: this.controlPlaneURL,
    });
  }

  private startConfigWatcher() {
    // Initial fetch
    this.fetchConfig();

    // Periodic refresh every 30 seconds
    setInterval(() => {
      this.fetchConfig();
    }, 30000);
  }

  private async fetchConfig() {
    try {
      const response = await axios.get(`${this.controlPlaneURL}/api/v1/rate-limit-policies`);
      const policies: RateLimitPolicy[] = response.data;

      // Update local cache
      for (const policy of policies) {
        this.limiter.updatePolicy(policy);
      }
    } catch (error: any) {
      console.error('Failed to fetch config from control plane:', error.message);
    }
  }
}

// Server setup
const app = express();
app.use(express.json());

const controlPlaneURL = process.env.CONTROL_PLANE_URL || 'http://localhost:3000';
const dataPlane = new DataPlaneAPI(controlPlaneURL);

app.post('/api/request', (req, res) => dataPlane.handleRequest(req, res));
app.post('/internal/config/rate-limits', (req, res) => dataPlane.updateConfig(req, res));
app.get('/health', (req, res) => dataPlane.health(req, res));
app.get('/metrics', (req, res) => dataPlane.metrics(req, res));

const port = process.env.PORT || 3001;
app.listen(port, () => {
  console.log(`Data plane running on port ${port}`);
  console.log(`Control plane URL: ${controlPlaneURL}`);
});
