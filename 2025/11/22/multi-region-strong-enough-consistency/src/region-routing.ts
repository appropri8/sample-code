/**
 * Region-aware routing middleware
 * 
 * Picks closest healthy region and routes to specific primary region
 * for "must-be-strong" endpoints
 */

interface Region {
  id: string;
  endpoint: string;
  health: 'healthy' | 'degraded' | 'unhealthy';
  latency?: number;
  lastChecked?: Date;
}

interface Request {
  headers: Record<string, string>;
  method: string;
  path: string;
  body?: any;
  userId?: string;
  region?: string;
}

interface RoutingConfig {
  defaultRegion: string;
  regions: Region[];
  strongConsistencyEndpoints: string[]; // Paths that need strong consistency
  userRegionMap?: Map<string, string>; // User ID -> region mapping
}

class RegionHealthChecker {
  private healthCache: Map<string, { health: Region['health']; lastChecked: Date }> = new Map();
  private checkInterval = 30000; // 30 seconds

  async checkHealth(region: Region): Promise<Region['health']> {
    const cached = this.healthCache.get(region.id);
    const now = new Date();

    // Use cached if recent
    if (cached && (now.getTime() - cached.lastChecked.getTime()) < this.checkInterval) {
      return cached.health;
    }

    try {
      // In production, make actual health check request
      const response = await fetch(`${region.endpoint}/health`, {
        method: 'GET',
        timeout: 5000
      });

      const health: Region['health'] = response.ok ? 'healthy' : 'degraded';
      
      this.healthCache.set(region.id, {
        health,
        lastChecked: now
      });

      return health;
    } catch (error) {
      this.healthCache.set(region.id, {
        health: 'unhealthy',
        lastChecked: now
      });
      return 'unhealthy';
    }
  }

  async checkAllRegions(regions: Region[]): Promise<Map<string, Region['health']>> {
    const results = new Map<string, Region['health']>();
    
    await Promise.all(
      regions.map(async region => {
        const health = await this.checkHealth(region);
        results.set(region.id, health);
      })
    );

    return results;
  }
}

class RegionRouter {
  constructor(
    private config: RoutingConfig,
    private healthChecker: RegionHealthChecker
  ) {}

  /**
   * Get region for user (sticky routing)
   */
  private getUserRegion(userId?: string): string | null {
    if (!userId) {
      return null;
    }

    // Check user region map first
    if (this.config.userRegionMap?.has(userId)) {
      return this.config.userRegionMap.get(userId)!;
    }

    // Hash user ID to region (consistent hashing)
    if (userId) {
      const hash = this.hashString(userId);
      const healthyRegions = this.config.regions.filter(
        r => r.health === 'healthy'
      );
      if (healthyRegions.length > 0) {
        return healthyRegions[hash % healthyRegions.length].id;
      }
    }

    return null;
  }

  /**
   * Get primary region for strong consistency
   */
  private getPrimaryRegion(userId?: string): string {
    // For strong consistency, route to user's primary region
    const userRegion = this.getUserRegion(userId);
    if (userRegion) {
      return userRegion;
    }

    // Fallback to default region
    return this.config.defaultRegion;
  }

  /**
   * Find closest healthy region
   */
  private async findClosestHealthyRegion(
    preferredRegion?: string
  ): Promise<Region | null> {
    // Update health status
    await this.healthChecker.checkAllRegions(this.config.regions);

    // Filter healthy regions
    const healthy = this.config.regions.filter(r => r.health === 'healthy');

    if (healthy.length === 0) {
      return null;
    }

    // If preferred region is healthy, use it
    if (preferredRegion) {
      const preferred = healthy.find(r => r.id === preferredRegion);
      if (preferred) {
        return preferred;
      }
    }

    // Otherwise, pick one (could use latency-based selection)
    return healthy[0];
  }

  /**
   * Route request to appropriate region
   */
  async route(request: Request): Promise<{ region: string; endpoint: string }> {
    const { method, path, userId } = request;

    // Check if this endpoint needs strong consistency
    const needsStrongConsistency = this.config.strongConsistencyEndpoints.some(
      endpoint => path.startsWith(endpoint)
    );

    if (needsStrongConsistency) {
      // Route to primary region for user
      const primaryRegionId = this.getPrimaryRegion(userId);
      const primaryRegion = this.config.regions.find(r => r.id === primaryRegionId);

      if (!primaryRegion) {
        throw new Error(`Primary region not found: ${primaryRegionId}`);
      }

      // Check health
      const health = await this.healthChecker.checkHealth(primaryRegion);
      if (health === 'unhealthy') {
        throw new Error(`Primary region ${primaryRegionId} is unhealthy`);
      }

      return {
        region: primaryRegionId,
        endpoint: primaryRegion.endpoint
      };
    }

    // For eventual consistency, use closest healthy region
    const userRegion = this.getUserRegion(userId);
    const closest = await this.findClosestHealthyRegion(userRegion);

    if (!closest) {
      throw new Error('No healthy regions available');
    }

    return {
      region: closest.id,
      endpoint: closest.endpoint
    };
  }

  /**
   * Simple hash function
   */
  private hashString(str: string): number {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash;
    }
    return Math.abs(hash);
  }
}

// Example middleware for Express-like framework
class RegionRoutingMiddleware {
  constructor(private router: RegionRouter) {}

  async handle(request: Request): Promise<Response> {
    try {
      // Route to appropriate region
      const { region, endpoint } = await this.router.route(request);

      // Forward request to region
      const targetUrl = `${endpoint}${request.path}`;
      
      const response = await fetch(targetUrl, {
        method: request.method,
        headers: {
          ...request.headers,
          'X-Routed-Region': region,
          'X-User-Region': request.userId ? this.router['getUserRegion'](request.userId) || '' : ''
        },
        body: request.body ? JSON.stringify(request.body) : undefined
      });

      // Add routing headers to response
      const responseHeaders: Record<string, string> = {
        'X-Data-Region': region,
        'X-Consistency-Level': this.router['config'].strongConsistencyEndpoints.some(
          e => request.path.startsWith(e)
        ) ? 'strong' : 'eventual'
      };

      return {
        status: response.status,
        headers: responseHeaders,
        body: await response.json()
      };
    } catch (error: any) {
      return {
        status: 503,
        headers: {
          'X-Error': 'RegionUnavailable',
          'Retry-After': '60'
        },
        body: {
          error: 'Service temporarily unavailable',
          message: error.message
        }
      };
    }
  }
}

// Example usage
async function example() {
  const regions: Region[] = [
    {
      id: 'us-east',
      endpoint: 'https://us-east.api.example.com',
      health: 'healthy'
    },
    {
      id: 'eu-west',
      endpoint: 'https://eu-west.api.example.com',
      health: 'healthy'
    },
    {
      id: 'ap-southeast',
      endpoint: 'https://ap-southeast.api.example.com',
      health: 'healthy'
    }
  ];

  const config: RoutingConfig = {
    defaultRegion: 'us-east',
    regions,
    strongConsistencyEndpoints: [
      '/api/accounts',
      '/api/payments',
      '/api/orders'
    ],
    userRegionMap: new Map([
      ['user-123', 'us-east'],
      ['user-456', 'ap-southeast']
    ])
  };

  const healthChecker = new RegionHealthChecker();
  const router = new RegionRouter(config, healthChecker);
  const middleware = new RegionRoutingMiddleware(router);

  // Request that needs strong consistency
  const strongRequest: Request = {
    headers: {},
    method: 'POST',
    path: '/api/payments',
    userId: 'user-123'
  };

  const strongResponse = await middleware.handle(strongRequest);
  console.log('Strong consistency request:', strongResponse);

  // Request that can use eventual consistency
  const eventualRequest: Request = {
    headers: {},
    method: 'GET',
    path: '/api/analytics',
    userId: 'user-123'
  };

  const eventualResponse = await middleware.handle(eventualRequest);
  console.log('Eventual consistency request:', eventualResponse);
}

export {
  RegionRouter,
  RegionHealthChecker,
  RegionRoutingMiddleware,
  Region,
  Request,
  RoutingConfig
};

