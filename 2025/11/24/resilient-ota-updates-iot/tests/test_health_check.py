"""Tests for health check reporting"""

import pytest
from datetime import datetime, timedelta
from src.health_check import HealthReporter, HealthStatus


def test_health_reporter_initialization():
    """Test health reporter initialization"""
    reporter = HealthReporter(
        device_id="device-12345",
        firmware_version="1.2.3",
        server_url="https://ota.example.com/api"
    )
    
    assert reporter.device_id == "device-12345"
    assert reporter.firmware_version == "1.2.3"
    assert reporter.max_boot_count == 3
    assert reporter.max_watchdog_resets == 5


def test_should_rollback_boot_count():
    """Test rollback trigger for excessive boot count"""
    reporter = HealthReporter(
        device_id="device-1",
        firmware_version="1.2.3",
        server_url="https://ota.example.com/api",
        max_boot_count=3
    )
    
    reporter.metrics.boot_count = 4  # Exceeds threshold
    assert reporter.should_rollback() is True


def test_should_rollback_watchdog():
    """Test rollback trigger for excessive watchdog resets"""
    reporter = HealthReporter(
        device_id="device-2",
        firmware_version="1.2.3",
        server_url="https://ota.example.com/api",
        max_watchdog_resets=5
    )
    
    reporter.metrics.watchdog_resets = 6  # Exceeds threshold
    assert reporter.should_rollback() is True


def test_should_not_rollback_healthy():
    """Test that healthy device doesn't trigger rollback"""
    reporter = HealthReporter(
        device_id="device-3",
        firmware_version="1.2.3",
        server_url="https://ota.example.com/api"
    )
    
    reporter.metrics.boot_count = 1
    reporter.metrics.watchdog_resets = 0
    reporter.metrics.can_connect_to_broker = True
    reporter.metrics.can_send_heartbeat = True
    
    assert reporter.should_rollback() is False


def test_get_health_status():
    """Test getting health status"""
    reporter = HealthReporter(
        device_id="device-4",
        firmware_version="1.2.3",
        server_url="https://ota.example.com/api"
    )
    
    reporter.metrics.boot_count = 0
    reporter.metrics.watchdog_resets = 0
    reporter.metrics.can_connect_to_broker = True
    reporter.metrics.can_send_heartbeat = True
    
    status = reporter.get_health_status()
    assert status == HealthStatus.OK


def test_get_metrics():
    """Test getting health metrics"""
    reporter = HealthReporter(
        device_id="device-5",
        firmware_version="1.2.3",
        server_url="https://ota.example.com/api"
    )
    
    metrics = reporter.get_metrics()
    assert metrics["device_id"] == "device-5"
    assert metrics["firmware_version"] == "1.2.3"
    assert "status" in metrics
    assert "boot_count" in metrics

