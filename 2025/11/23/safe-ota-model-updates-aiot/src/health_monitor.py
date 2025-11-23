"""Health monitor for device and model health tracking."""

import time
from typing import Dict, Any, Optional
import psutil


class HealthMonitor:
    """Monitors device health metrics."""
    
    def __init__(self):
        """Initialize health monitor."""
        self.inference_count = 0
        self.error_count = 0
        self.latency_sum = 0.0
        self.start_time = time.time()
    
    def record_inference(self, latency_ms: float, success: bool = True):
        """Record a single inference.
        
        Args:
            latency_ms: Inference latency in milliseconds
            success: Whether inference succeeded
        """
        self.inference_count += 1
        if success:
            self.latency_sum += latency_ms
        else:
            self.error_count += 1
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current health metrics.
        
        Returns:
            Dictionary of current metrics
        """
        elapsed = time.time() - self.start_time
        
        avg_latency = 0.0
        if self.inference_count > self.error_count:
            avg_latency_count = self.inference_count - self.error_count
            avg_latency = self.latency_sum / avg_latency_count
        
        error_rate = 0.0
        if self.inference_count > 0:
            error_rate = self.error_count / self.inference_count
        
        return {
            "avg_latency_ms": avg_latency,
            "num_inferences": self.inference_count,
            "num_errors": self.error_count,
            "error_rate": error_rate,
            "cpu_percent": self.get_cpu_usage(),
            "ram_percent": self.get_ram_usage(),
            "uptime_seconds": elapsed
        }
    
    def get_cpu_usage(self) -> float:
        """Get current CPU usage percentage.
        
        Returns:
            CPU usage percentage
        """
        try:
            return psutil.cpu_percent(interval=1)
        except Exception:
            return 0.0
    
    def get_ram_usage(self) -> float:
        """Get current RAM usage percentage.
        
        Returns:
            RAM usage percentage
        """
        try:
            return psutil.virtual_memory().percent
        except Exception:
            return 0.0
    
    def check_health(self, metrics: Dict[str, Any], thresholds: Dict[str, Any]) -> bool:
        """Check if metrics are within thresholds.
        
        Args:
            metrics: Current metrics
            thresholds: Health check thresholds
            
        Returns:
            True if healthy, False otherwise
        """
        # Check CPU
        max_cpu = thresholds.get("max_cpu_percent", 100)
        if metrics.get("cpu_percent", 0) > max_cpu:
            return False
        
        # Check RAM
        max_ram = thresholds.get("max_ram_percent", 100)
        if metrics.get("ram_percent", 0) > max_ram:
            return False
        
        # Check latency
        max_latency = thresholds.get("max_latency_ms", 1000)
        if metrics.get("avg_latency_ms", 0) > max_latency:
            return False
        
        # Check error rate
        max_error_rate = thresholds.get("max_error_rate", 1.0)
        if metrics.get("error_rate", 0) > max_error_rate:
            return False
        
        return True
    
    def reset(self):
        """Reset metrics counters."""
        self.inference_count = 0
        self.error_count = 0
        self.latency_sum = 0.0
        self.start_time = time.time()

