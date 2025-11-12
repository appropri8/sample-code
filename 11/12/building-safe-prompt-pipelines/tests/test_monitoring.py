"""Tests for monitoring and anomaly detection"""

import pytest
from datetime import datetime, timedelta
from src.monitoring import AnomalyDetector, PipelineMonitor, PipelineLogger
from src.pipeline import PromptMetadata

def test_anomaly_detector_initialization():
    """Test anomaly detector initialization"""
    detector = AnomalyDetector()
    
    assert detector.alert_threshold == 5
    assert len(detector.request_history) == 0

def test_anomaly_detector_detects_suspicious_patterns():
    """Test that anomaly detector detects suspicious patterns"""
    detector = AnomalyDetector()
    
    metadata = PromptMetadata(
        input_length=100,
        sanitised_length=95,
        suspicious_patterns=["pattern1", "pattern2"],
        timestamp=datetime.now().isoformat()
    )
    
    result = detector.check_anomaly("user1", metadata, "test input")
    
    assert result["is_anomaly"] is True or result["risk_score"] > 0
    assert "reasons" in result

def test_anomaly_detector_detects_long_input():
    """Test detection of unusually long input"""
    detector = AnomalyDetector()
    
    metadata = PromptMetadata(
        input_length=2000,  # Unusually long
        sanitised_length=1950,
        suspicious_patterns=[],
        timestamp=datetime.now().isoformat()
    )
    
    result = detector.check_anomaly("user1", metadata, "A" * 2000)
    
    assert result["risk_score"] > 0

def test_anomaly_detector_rate_limiting():
    """Test rate limiting detection"""
    detector = AnomalyDetector()
    
    metadata = PromptMetadata(
        input_length=100,
        sanitised_length=95,
        suspicious_patterns=[],
        timestamp=datetime.now().isoformat()
    )
    
    # Simulate many requests
    for i in range(15):
        detector.check_anomaly("user1", metadata, f"test input {i}")
    
    # Check that rate limiting is detected
    result = detector.check_anomaly("user1", metadata, "test input")
    
    # Should have high risk due to rate
    assert result["risk_score"] > 0

def test_pipeline_monitor_initialization():
    """Test pipeline monitor initialization"""
    monitor = PipelineMonitor()
    
    assert monitor.metrics["total_requests"] == 0
    assert monitor.metrics["suspicious_requests"] == 0

def test_pipeline_monitor_updates_metrics():
    """Test that monitor updates metrics correctly"""
    monitor = PipelineMonitor()
    
    monitor.update_metrics(
        has_suspicious_patterns=True,
        anomaly_result={"risk_score": 0.5, "is_anomaly": True}
    )
    
    assert monitor.metrics["total_requests"] == 1
    assert monitor.metrics["suspicious_requests"] == 1
    assert monitor.metrics["average_risk_score"] > 0

def test_pipeline_monitor_calculates_anomaly_rate():
    """Test anomaly rate calculation"""
    monitor = PipelineMonitor()
    
    # Add some requests
    for i in range(10):
        monitor.update_metrics(
            has_suspicious_patterns=(i % 2 == 0),  # Half suspicious
            anomaly_result={"risk_score": 0.3, "is_anomaly": False}
        )
    
    metrics = monitor.get_metrics()
    assert metrics["anomaly_rate"] > 0
    assert metrics["anomaly_rate"] <= 1.0

