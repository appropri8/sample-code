"""Tests for health monitor."""

import pytest
import time
from src.health_monitor import HealthMonitor


class TestHealthMonitor:
    """Test health monitor functionality."""
    
    @pytest.fixture
    def monitor(self):
        """Create health monitor for testing."""
        return HealthMonitor()
    
    def test_record_inference(self, monitor):
        """Test inference recording."""
        monitor.record_inference(50.0, success=True)
        monitor.record_inference(60.0, success=True)
        monitor.record_inference(70.0, success=False)
        
        metrics = monitor.get_current_metrics()
        
        assert metrics["num_inferences"] == 3
        assert metrics["num_errors"] == 1
        assert metrics["error_rate"] == pytest.approx(1.0 / 3.0, rel=0.01)
        assert metrics["avg_latency_ms"] == pytest.approx(55.0, rel=0.01)  # (50 + 60) / 2
    
    def test_check_health(self, monitor):
        """Test health checking."""
        # Record some normal inferences
        for _ in range(10):
            monitor.record_inference(45.0, success=True)
        
        metrics = monitor.get_current_metrics()
        
        thresholds = {
            "max_cpu_percent": 80,
            "max_ram_percent": 90,
            "max_latency_ms": 200,
            "max_error_rate": 0.01
        }
        
        # Should be healthy
        assert monitor.check_health(metrics, thresholds)
        
        # Test high CPU
        high_cpu_metrics = metrics.copy()
        high_cpu_metrics["cpu_percent"] = 85.0
        assert not monitor.check_health(high_cpu_metrics, thresholds)
        
        # Test high latency
        high_latency_metrics = metrics.copy()
        high_latency_metrics["avg_latency_ms"] = 250.0
        assert not monitor.check_health(high_latency_metrics, thresholds)
        
        # Test high error rate
        high_error_metrics = metrics.copy()
        high_error_metrics["error_rate"] = 0.05
        assert not monitor.check_health(high_error_metrics, thresholds)
    
    def test_reset(self, monitor):
        """Test reset functionality."""
        monitor.record_inference(50.0, success=True)
        monitor.record_inference(60.0, success=False)
        
        metrics_before = monitor.get_current_metrics()
        assert metrics_before["num_inferences"] == 2
        
        monitor.reset()
        
        metrics_after = monitor.get_current_metrics()
        assert metrics_after["num_inferences"] == 0
        assert metrics_after["num_errors"] == 0

