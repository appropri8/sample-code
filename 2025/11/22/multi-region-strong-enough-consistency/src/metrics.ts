/**
 * Metric and SLO instrumentation
 * 
 * Emits metrics when reads are stale, logs conflict events,
 * and tracks SLO compliance
 */

interface Metric {
  name: string;
  value: number;
  tags: Record<string, string>;
  timestamp: Date;
}

interface ConflictEvent {
  entityId: string;
  entityType: string;
  conflictType: 'version' | 'merge' | 'data';
  region: string;
  timestamp: Date;
}

class MetricsCollector {
  private metrics: Metric[] = [];

  /**
   * Emit a counter metric
   */
  increment(name: string, tags: Record<string, string> = {}): void {
    this.metrics.push({
      name,
      value: 1,
      tags,
      timestamp: new Date()
    });
  }

  /**
   * Emit a gauge metric
   */
  gauge(name: string, value: number, tags: Record<string, string> = {}): void {
    this.metrics.push({
      name,
      value,
      tags,
      timestamp: new Date()
    });
  }

  /**
   * Emit a histogram metric
   */
  histogram(name: string, value: number, tags: Record<string, string> = {}): void {
    this.metrics.push({
      name,
      value,
      tags,
      timestamp: new Date()
    });
  }

  /**
   * Get all metrics
   */
  getMetrics(): Metric[] {
    return [...this.metrics];
  }

  /**
   * Clear metrics (for testing)
   */
  clear(): void {
    this.metrics = [];
  }
}

class SLOTracker {
  constructor(private metrics: MetricsCollector) {}

  /**
   * Track read freshness SLO: "95% of reads are fresh within 2 seconds"
   */
  trackReadFreshness(
    entityType: string,
    region: string,
    updatedAt: Date,
    thresholdMs: number = 2000
  ): void {
    const now = new Date();
    const age = now.getTime() - updatedAt.getTime();
    const isFresh = age <= thresholdMs;

    if (isFresh) {
      this.metrics.increment('slo.reads_fresh.success', {
        entity_type: entityType,
        region
      });
    } else {
      this.metrics.increment('slo.reads_fresh.violation', {
        entity_type: entityType,
        region,
        age_ms: age.toString()
      });
    }

    // Track age distribution
    this.metrics.histogram('reads.freshness_age_ms', age, {
      entity_type: entityType,
      region
    });
  }

  /**
   * Track consistency level SLO: "99.9% of balance reads are strongly consistent"
   */
  trackConsistencyLevel(
    entityType: string,
    region: string,
    consistencyLevel: 'strong' | 'eventual'
  ): void {
    if (consistencyLevel === 'strong') {
      this.metrics.increment('slo.balance_consistency.success', {
        entity_type: entityType,
        region
      });
    } else {
      this.metrics.increment('slo.balance_consistency.violation', {
        entity_type: entityType,
        region
      });
    }
  }

  /**
   * Track region availability SLO: "99.95% region availability"
   */
  trackRegionAvailability(region: string, isAvailable: boolean): void {
    this.metrics.gauge('regions.availability', isAvailable ? 1 : 0, {
      region
    });
  }

  /**
   * Calculate SLO compliance rate
   */
  calculateComplianceRate(metricName: string): number {
    const metrics = this.metrics.getMetrics();
    const relevant = metrics.filter(m => m.name === metricName);
    
    if (relevant.length === 0) {
      return 1.0; // No data, assume compliant
    }

    const successes = relevant.filter(m => m.name.includes('.success')).length;
    return successes / relevant.length;
  }
}

class ConflictLogger {
  private conflicts: ConflictEvent[] = [];

  /**
   * Log conflict event
   */
  logConflict(event: ConflictEvent): void {
    this.conflicts.push(event);

    // In production, send to logging system
    console.log('Conflict detected:', {
      entityId: event.entityId,
      entityType: event.entityType,
      conflictType: event.conflictType,
      region: event.region,
      timestamp: event.timestamp
    });
  }

  /**
   * Get conflicts
   */
  getConflicts(): ConflictEvent[] {
    return [...this.conflicts];
  }

  /**
   * Get conflict rate
   */
  getConflictRate(entityType?: string, timeWindowMs?: number): number {
    let conflicts = this.conflicts;

    // Filter by entity type if provided
    if (entityType) {
      conflicts = conflicts.filter(c => c.entityType === entityType);
    }

    // Filter by time window if provided
    if (timeWindowMs) {
      const cutoff = new Date(Date.now() - timeWindowMs);
      conflicts = conflicts.filter(c => c.timestamp >= cutoff);
    }

    // In production, you'd compare against total operations
    // For this example, return a simple rate
    return conflicts.length / 1000; // Simplified
  }
}

class ObservabilityService {
  constructor(
    private metrics: MetricsCollector,
    private sloTracker: SLOTracker,
    private conflictLogger: ConflictLogger
  ) {}

  /**
   * Track stale read
   */
  trackStaleRead(
    entityType: string,
    currentRegion: string,
    dataRegion: string,
    age: number
  ): void {
    this.metrics.increment('reads.stale', {
      entity_type: entityType,
      region: currentRegion,
      source_region: dataRegion,
      age_ms: age.toString()
    });

    // Track freshness SLO
    const updatedAt = new Date(Date.now() - age);
    this.sloTracker.trackReadFreshness(entityType, currentRegion, updatedAt);
  }

  /**
   * Track cross-region latency
   */
  trackCrossRegionLatency(
    sourceRegion: string,
    targetRegion: string,
    latencyMs: number
  ): void {
    this.metrics.histogram('reads.cross_region_latency', latencyMs, {
      source_region: sourceRegion,
      target_region: targetRegion
    });
  }

  /**
   * Track conflict
   */
  trackConflict(
    entityId: string,
    entityType: string,
    conflictType: ConflictEvent['conflictType'],
    region: string
  ): void {
    this.metrics.increment('conflicts.detected', {
      entity_type: entityType,
      conflict_type: conflictType,
      region
    });

    this.conflictLogger.logConflict({
      entityId,
      entityType,
      conflictType,
      region,
      timestamp: new Date()
    });
  }

  /**
   * Track region health
   */
  trackRegionHealth(region: string, isHealthy: boolean): void {
    this.metrics.gauge('regions.health', isHealthy ? 1 : 0, {
      region
    });

    this.sloTracker.trackRegionAvailability(region, isHealthy);
  }

  /**
   * Check SLO violations and alert
   */
  checkSLOViolations(): void {
    const freshnessCompliance = this.sloTracker.calculateComplianceRate('slo.reads_fresh');
    if (freshnessCompliance < 0.95) {
      console.warn('SLO violation: reads freshness', {
        compliance: freshnessCompliance,
        threshold: 0.95
      });
    }

    const consistencyCompliance = this.sloTracker.calculateComplianceRate('slo.balance_consistency');
    if (consistencyCompliance < 0.999) {
      console.warn('SLO violation: balance consistency', {
        compliance: consistencyCompliance,
        threshold: 0.999
      });
    }
  }
}

// Example usage
function example() {
  const metrics = new MetricsCollector();
  const sloTracker = new SLOTracker(metrics);
  const conflictLogger = new ConflictLogger();
  const observability = new ObservabilityService(metrics, sloTracker, conflictLogger);

  // Track stale read
  observability.trackStaleRead('account', 'us-east', 'ap-southeast', 3000);

  // Track cross-region latency
  observability.trackCrossRegionLatency('us-east', 'ap-southeast', 250);

  // Track conflict
  observability.trackConflict('account-123', 'account', 'version', 'us-east');

  // Track region health
  observability.trackRegionHealth('us-east', true);
  observability.trackRegionHealth('ap-southeast', false);

  // Check SLO violations
  observability.checkSLOViolations();

  // Get metrics
  const allMetrics = metrics.getMetrics();
  console.log('Metrics:', allMetrics);

  // Get conflicts
  const conflicts = conflictLogger.getConflicts();
  console.log('Conflicts:', conflicts);
}

export {
  MetricsCollector,
  SLOTracker,
  ConflictLogger,
  ObservabilityService,
  Metric,
  ConflictEvent
};

