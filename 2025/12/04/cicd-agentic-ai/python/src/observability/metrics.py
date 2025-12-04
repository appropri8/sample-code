"""Metrics collection for agentic AI systems"""
from typing import Dict, Any
from collections import defaultdict


class MetricsCollector:
    """Collect metrics for agents and workflows"""
    
    def __init__(self):
        self.counters = defaultdict(int)
        self.gauges = {}
        self.histograms = defaultdict(list)
    
    def increment(self, metric: str, tags: Dict[str, str] = None):
        """Increment counter"""
        key = self._make_key(metric, tags)
        self.counters[key] += 1
    
    def gauge(self, metric: str, value: float, tags: Dict[str, str] = None):
        """Set gauge value"""
        key = self._make_key(metric, tags)
        self.gauges[key] = value
    
    def histogram(self, metric: str, value: float, tags: Dict[str, str] = None):
        """Record histogram value"""
        key = self._make_key(metric, tags)
        self.histograms[key].append(value)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all metrics"""
        return {
            "counters": dict(self.counters),
            "gauges": dict(self.gauges),
            "histograms": {
                k: {
                    "count": len(v),
                    "min": min(v) if v else 0,
                    "max": max(v) if v else 0,
                    "avg": sum(v) / len(v) if v else 0,
                    "p95": sorted(v)[int(len(v) * 0.95)] if len(v) > 0 else 0
                }
                for k, v in self.histograms.items()
            }
        }
    
    def _make_key(self, metric: str, tags: Dict[str, str] = None) -> str:
        """Make metric key with tags"""
        if not tags:
            return metric
        tag_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{metric}[{tag_str}]"
    
    def reset(self):
        """Reset all metrics"""
        self.counters.clear()
        self.gauges.clear()
        self.histograms.clear()


# Global metrics instance
metrics = MetricsCollector()


def track_agent_execution(
    agent_version: str,
    success: bool,
    latency_ms: int,
    tokens_used: int = 0,
    cost: float = 0.0
):
    """Track agent execution metrics"""
    metrics.increment("agent.executions", {"version": agent_version})
    metrics.increment(
        "agent.executions",
        {"version": agent_version, "status": "success" if success else "error"}
    )
    metrics.histogram("agent.latency_ms", latency_ms, {"version": agent_version})
    
    if tokens_used > 0:
        metrics.histogram("agent.tokens_used", tokens_used, {"version": agent_version})
    
    if cost > 0:
        metrics.gauge("agent.cost", cost, {"version": agent_version})

