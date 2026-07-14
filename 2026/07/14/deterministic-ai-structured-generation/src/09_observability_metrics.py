"""
Example 9: Observability Metrics

Tracks and exports key metrics:
- Validation success rate
- Retry rate
- Parse failure rate
- Latency percentiles
- Schema drift
"""

import time
from collections import defaultdict
from typing import Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ExtractionMetrics:
    """Metrics for a single extraction attempt"""
    
    timestamp: datetime
    success: bool
    validation_passed: bool
    parse_passed: bool
    retry_count: int
    latency_ms: float
    schema_version: str
    error_type: str | None = None
    fields_populated: set[str] = field(default_factory=set)


class MetricsCollector:
    """Collects and aggregates extraction metrics"""
    
    def __init__(self):
        self.metrics: list[ExtractionMetrics] = []
        self.field_usage = defaultdict(int)
        self.error_counts = defaultdict(int)
    
    def record(self, metric: ExtractionMetrics):
        """Record a single extraction attempt"""
        self.metrics.append(metric)
        
        # Track field usage
        for field in metric.fields_populated:
            self.field_usage[field] += 1
        
        # Track error types
        if metric.error_type:
            self.error_counts[metric.error_type] += 1
    
    def validation_success_rate(self) -> float:
        """Calculate validation success rate"""
        if not self.metrics:
            return 0.0
        
        successful = sum(1 for m in self.metrics if m.validation_passed)
        return successful / len(self.metrics)
    
    def retry_rate(self) -> float:
        """Calculate retry rate"""
        if not self.metrics:
            return 0.0
        
        retries = sum(1 for m in self.metrics if m.retry_count > 0)
        return retries / len(self.metrics)
    
    def parse_failure_rate(self) -> float:
        """Calculate parse failure rate"""
        if not self.metrics:
            return 0.0
        
        failures = sum(1 for m in self.metrics if not m.parse_passed)
        return failures / len(self.metrics)
    
    def latency_percentiles(self) -> dict[str, float]:
        """Calculate latency percentiles"""
        if not self.metrics:
            return {"p50": 0.0, "p95": 0.0, "p99": 0.0}
        
        latencies = sorted(m.latency_ms for m in self.metrics)
        n = len(latencies)
        
        return {
            "p50": latencies[int(n * 0.50)],
            "p95": latencies[int(n * 0.95)],
            "p99": latencies[int(n * 0.99)],
            "min": latencies[0],
            "max": latencies[-1],
            "avg": sum(latencies) / n
        }
    
    def field_population_rates(self) -> dict[str, float]:
        """Calculate how often each field is populated"""
        if not self.metrics:
            return {}
        
        total = len(self.metrics)
        return {
            field: count / total
            for field, count in self.field_usage.items()
        }
    
    def top_errors(self, limit: int = 5) -> list[tuple[str, int]]:
        """Get most common error types"""
        return sorted(
            self.error_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:limit]
    
    def summary(self) -> dict[str, Any]:
        """Get complete metrics summary"""
        return {
            "total_extractions": len(self.metrics),
            "validation_success_rate": self.validation_success_rate(),
            "retry_rate": self.retry_rate(),
            "parse_failure_rate": self.parse_failure_rate(),
            "latency_percentiles": self.latency_percentiles(),
            "field_population_rates": self.field_population_rates(),
            "top_errors": dict(self.top_errors())
        }
    
    def export_prometheus(self) -> str:
        """Export metrics in Prometheus format"""
        lines = []
        
        # Validation success rate
        lines.append("# HELP extraction_validation_success_rate Validation success rate")
        lines.append("# TYPE extraction_validation_success_rate gauge")
        lines.append(f"extraction_validation_success_rate {self.validation_success_rate():.4f}")
        
        # Retry rate
        lines.append("# HELP extraction_retry_rate Retry rate")
        lines.append("# TYPE extraction_retry_rate gauge")
        lines.append(f"extraction_retry_rate {self.retry_rate():.4f}")
        
        # Parse failure rate
        lines.append("# HELP extraction_parse_failure_rate Parse failure rate")
        lines.append("# TYPE extraction_parse_failure_rate gauge")
        lines.append(f"extraction_parse_failure_rate {self.parse_failure_rate():.4f}")
        
        # Latency percentiles
        latencies = self.latency_percentiles()
        for percentile, value in latencies.items():
            lines.append(f"# HELP extraction_latency_{percentile} Latency {percentile}")
            lines.append(f"# TYPE extraction_latency_{percentile} gauge")
            lines.append(f"extraction_latency_{percentile} {value:.2f}")
        
        return "\n".join(lines)


class AlertingThresholds:
    """Define alerting thresholds for metrics"""
    
    def __init__(
        self,
        min_validation_success_rate: float = 0.7,
        max_retry_rate: float = 0.3,
        max_parse_failure_rate: float = 0.1,
        max_p95_latency_ms: float = 5000.0
    ):
        self.min_validation_success_rate = min_validation_success_rate
        self.max_retry_rate = max_retry_rate
        self.max_parse_failure_rate = max_parse_failure_rate
        self.max_p95_latency_ms = max_p95_latency_ms
    
    def check_alerts(self, collector: MetricsCollector) -> list[str]:
        """Check if any metrics exceed thresholds"""
        alerts = []
        
        # Validation success rate
        vsr = collector.validation_success_rate()
        if vsr < self.min_validation_success_rate:
            alerts.append(
                f"Validation success rate {vsr:.2%} below threshold "
                f"{self.min_validation_success_rate:.2%}"
            )
        
        # Retry rate
        rr = collector.retry_rate()
        if rr > self.max_retry_rate:
            alerts.append(
                f"Retry rate {rr:.2%} above threshold {self.max_retry_rate:.2%}"
            )
        
        # Parse failure rate
        pfr = collector.parse_failure_rate()
        if pfr > self.max_parse_failure_rate:
            alerts.append(
                f"Parse failure rate {pfr:.2%} above threshold "
                f"{self.max_parse_failure_rate:.2%}"
            )
        
        # P95 latency
        latencies = collector.latency_percentiles()
        if latencies["p95"] > self.max_p95_latency_ms:
            alerts.append(
                f"P95 latency {latencies['p95']:.2f}ms above threshold "
                f"{self.max_p95_latency_ms:.2f}ms"
            )
        
        return alerts


def demonstrate_metrics():
    """Demonstrate metrics collection and alerting"""
    
    print("=" * 60)
    print("Example 9: Observability Metrics")
    print("=" * 60)
    
    # Create collector
    collector = MetricsCollector()
    
    # Simulate some extraction attempts
    print("\n1. Recording Sample Metrics:")
    
    # Successful extractions
    for i in range(80):
        collector.record(ExtractionMetrics(
            timestamp=datetime.now(),
            success=True,
            validation_passed=True,
            parse_passed=True,
            retry_count=0,
            latency_ms=500 + (i * 10),
            schema_version="2.0",
            fields_populated={"title", "priority", "category"}
        ))
    
    # Extractions with retries
    for i in range(12):
        collector.record(ExtractionMetrics(
            timestamp=datetime.now(),
            success=True,
            validation_passed=True,
            parse_passed=True,
            retry_count=1,
            latency_ms=1200 + (i * 50),
            schema_version="2.0",
            error_type="validation_error",
            fields_populated={"title", "priority", "category"}
        ))
    
    # Parse failures
    for i in range(5):
        collector.record(ExtractionMetrics(
            timestamp=datetime.now(),
            success=False,
            validation_passed=False,
            parse_passed=False,
            retry_count=2,
            latency_ms=2000,
            schema_version="2.0",
            error_type="parse_error"
        ))
    
    # Validation failures
    for i in range(3):
        collector.record(ExtractionMetrics(
            timestamp=datetime.now(),
            success=False,
            validation_passed=False,
            parse_passed=True,
            retry_count=2,
            latency_ms=1800,
            schema_version="2.0",
            error_type="invalid_enum"
        ))
    
    print(f"   Recorded {len(collector.metrics)} extraction attempts")
    
    # Show metrics summary
    print("\n2. Metrics Summary:")
    summary = collector.summary()
    print(f"   Total extractions: {summary['total_extractions']}")
    print(f"   Validation success rate: {summary['validation_success_rate']:.2%}")
    print(f"   Retry rate: {summary['retry_rate']:.2%}")
    print(f"   Parse failure rate: {summary['parse_failure_rate']:.2%}")
    
    print(f"\n3. Latency Percentiles:")
    for key, value in summary['latency_percentiles'].items():
        print(f"   {key}: {value:.2f}ms")
    
    print(f"\n4. Field Population Rates:")
    for field, rate in summary['field_population_rates'].items():
        print(f"   {field}: {rate:.2%}")
    
    print(f"\n5. Top Errors:")
    for error, count in summary['top_errors'].items():
        print(f"   {error}: {count} occurrences")
    
    # Check alerts
    print(f"\n6. Alert Check:")
    thresholds = AlertingThresholds()
    alerts = thresholds.check_alerts(collector)
    if alerts:
        print("   🚨 Alerts triggered:")
        for alert in alerts:
            print(f"     - {alert}")
    else:
        print("   ✅ All metrics within thresholds")
    
    # Export Prometheus metrics
    print(f"\n7. Prometheus Export (first 10 lines):")
    prom_metrics = collector.export_prometheus()
    for line in prom_metrics.split('\n')[:10]:
        print(f"   {line}")
    
    print("\n" + "=" * 60)
    print("Observability metrics demonstration complete!")
    print("=" * 60)


if __name__ == "__main__":
    demonstrate_metrics()
