"""Observability utilities for failure-first agents."""

import time
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class LogEntry:
    """Structured log entry."""
    trace_id: str
    user_id: Optional[str]
    workflow_id: Optional[str]
    step_name: Optional[str]
    tool_name: Optional[str]
    error_type: Optional[str]
    error_message: Optional[str]
    retries: int
    duration_ms: float
    timestamp: float
    context: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)


class MetricsCollector:
    """Collect metrics for observability."""
    
    def __init__(self):
        self.error_counts = defaultdict(int)
        self.retry_counts = defaultdict(int)
        self.tool_durations = defaultdict(list)
        self.workflow_durations = []
    
    def record_error(self, error_type: str, tool_name: str):
        """Record an error."""
        key = f"{error_type}:{tool_name}"
        self.error_counts[key] += 1
    
    def record_retry(self, workflow_id: str):
        """Record a retry."""
        self.retry_counts[workflow_id] += 1
    
    def record_tool_duration(self, tool_name: str, duration_ms: float):
        """Record tool duration."""
        self.tool_durations[tool_name].append(duration_ms)
    
    def record_workflow_duration(self, duration_ms: float):
        """Record workflow duration."""
        self.workflow_durations.append(duration_ms)
    
    def get_error_rate_by_tool(self) -> Dict[str, int]:
        """Get error rate by tool."""
        by_tool = defaultdict(int)
        for key, count in self.error_counts.items():
            _, tool = key.split(":", 1)
            by_tool[tool] += count
        return dict(by_tool)
    
    def get_average_retries(self) -> float:
        """Get average retries per workflow."""
        if not self.retry_counts:
            return 0.0
        return sum(self.retry_counts.values()) / len(self.retry_counts)
    
    def get_top_errors(self, limit: int = 10) -> List[tuple]:
        """Get top error types."""
        error_types = defaultdict(int)
        for key, count in self.error_counts.items():
            error_type, _ = key.split(":", 1)
            error_types[error_type] += count
        
        return sorted(error_types.items(), key=lambda x: x[1], reverse=True)[:limit]


class AlertManager:
    """Simple alert manager."""
    
    def __init__(self, metrics: MetricsCollector):
        self.metrics = metrics
        self.alerts_sent = []
    
    def check_alerts(self):
        """Check for conditions that need alerts."""
        # Check for error spikes
        error_rates = self.metrics.get_error_rate_by_tool()
        for tool, count in error_rates.items():
            if count > 10:  # Threshold
                self._send_alert(f"Spike in errors for {tool}: {count} errors")
        
        # Check for high retry rate
        avg_retries = self.metrics.get_average_retries()
        if avg_retries > 2.0:
            self._send_alert(f"High average retry rate: {avg_retries:.2f}")
    
    def _send_alert(self, message: str):
        """Send an alert."""
        logger.error(f"ALERT: {message}")
        self.alerts_sent.append({
            "message": message,
            "timestamp": time.time()
        })


class StructuredLogger:
    """Structured logger for agent operations."""
    
    def __init__(self, metrics: Optional[MetricsCollector] = None):
        self.metrics = metrics or MetricsCollector()
    
    def log_step(
        self,
        trace_id: str,
        step_name: str,
        tool_name: Optional[str] = None,
        user_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        duration_ms: Optional[float] = None,
        error: Optional[Exception] = None,
        retries: int = 0,
        context: Optional[Dict] = None
    ):
        """Log a step execution."""
        entry = LogEntry(
            trace_id=trace_id,
            user_id=user_id,
            workflow_id=workflow_id,
            step_name=step_name,
            tool_name=tool_name,
            error_type=type(error).__name__ if error else None,
            error_message=str(error) if error else None,
            retries=retries,
            duration_ms=duration_ms or 0.0,
            timestamp=time.time(),
            context=context or {}
        )
        
        # Log to standard logger
        if error:
            logger.error(f"Step failed: {entry.to_dict()}")
        else:
            logger.info(f"Step completed: {entry.to_dict()}")
        
        # Record metrics
        if error:
            self.metrics.record_error(
                type(error).__name__,
                tool_name or "unknown"
            )
        
        if retries > 0:
            self.metrics.record_retry(workflow_id or trace_id)
        
        if duration_ms and tool_name:
            self.metrics.record_tool_duration(tool_name, duration_ms)
    
    def log_workflow(
        self,
        trace_id: str,
        workflow_id: str,
        status: str,
        duration_ms: float,
        steps_executed: int,
        error: Optional[Exception] = None
    ):
        """Log workflow completion."""
        entry = {
            "trace_id": trace_id,
            "workflow_id": workflow_id,
            "status": status,
            "duration_ms": duration_ms,
            "steps_executed": steps_executed,
            "error": str(error) if error else None,
            "timestamp": time.time()
        }
        
        if error:
            logger.error(f"Workflow failed: {entry}")
        else:
            logger.info(f"Workflow completed: {entry}")
        
        self.metrics.record_workflow_duration(duration_ms)


# Example usage
if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Create logger and metrics
    metrics = MetricsCollector()
    logger = StructuredLogger(metrics)
    alert_manager = AlertManager(metrics)
    
    # Simulate some operations
    trace_id = "trace_123"
    workflow_id = "workflow_456"
    
    # Log successful step
    logger.log_step(
        trace_id=trace_id,
        step_name="call_search",
        tool_name="search_api",
        workflow_id=workflow_id,
        duration_ms=150.0
    )
    
    # Log failed step with retries
    logger.log_step(
        trace_id=trace_id,
        step_name="call_payment",
        tool_name="payment_gateway",
        workflow_id=workflow_id,
        duration_ms=5000.0,
        error=Exception("Timeout"),
        retries=2
    )
    
    # Log workflow completion
    logger.log_workflow(
        trace_id=trace_id,
        workflow_id=workflow_id,
        status="failed",
        duration_ms=5150.0,
        steps_executed=2,
        error=Exception("Workflow failed")
    )
    
    # Check alerts
    alert_manager.check_alerts()
    
    # Print metrics
    print(f"Error rate by tool: {metrics.get_error_rate_by_tool()}")
    print(f"Average retries: {metrics.get_average_retries():.2f}")
    print(f"Top errors: {metrics.get_top_errors()}")

