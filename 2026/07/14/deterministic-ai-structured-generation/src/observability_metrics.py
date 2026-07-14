"""
Observability Metrics

Tracks extraction metrics for monitoring and alerting
"""

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
