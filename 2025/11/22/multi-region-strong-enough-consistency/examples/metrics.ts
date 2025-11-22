import {
  MetricsCollector,
  SLOTracker,
  ConflictLogger,
  ObservabilityService
} from '../src/metrics';

/**
 * Example: Metric and SLO instrumentation
 * 
 * Demonstrates how to track metrics, conflicts, and SLO compliance
 */

function main() {
  const metrics = new MetricsCollector();
  const sloTracker = new SLOTracker(metrics);
  const conflictLogger = new ConflictLogger();
  const observability = new ObservabilityService(
    metrics,
    sloTracker,
    conflictLogger
  );

  console.log('=== Tracking Stale Read ===');
  const updatedAt = new Date(Date.now() - 3000); // 3 seconds ago
  observability.trackStaleRead('account', 'us-east', 'ap-southeast', 3000);
  console.log('Stale read tracked (3 seconds old)');

  console.log('\n=== Tracking Cross-Region Latency ===');
  observability.trackCrossRegionLatency('us-east', 'ap-southeast', 250);
  console.log('Cross-region latency tracked: 250ms');

  console.log('\n=== Tracking Conflict ===');
  observability.trackConflict('account-123', 'account', 'version', 'us-east');
  console.log('Version conflict tracked');

  console.log('\n=== Tracking Region Health ===');
  observability.trackRegionHealth('us-east', true);
  observability.trackRegionHealth('ap-southeast', false);
  console.log('Region health tracked');

  console.log('\n=== Checking SLO Violations ===');
  observability.checkSLOViolations();

  console.log('\n=== All Metrics ===');
  const allMetrics = metrics.getMetrics();
  allMetrics.forEach(metric => {
    console.log(`${metric.name}: ${metric.value}`, metric.tags);
  });

  console.log('\n=== Conflicts ===');
  const conflicts = conflictLogger.getConflicts();
  conflicts.forEach(conflict => {
    console.log(`${conflict.entityType} ${conflict.entityId}: ${conflict.conflictType} in ${conflict.region}`);
  });

  console.log('\n=== Conflict Rate ===');
  const conflictRate = conflictLogger.getConflictRate('account', 60000);
  console.log(`Conflict rate (last 60s): ${conflictRate}`);
}

main();

