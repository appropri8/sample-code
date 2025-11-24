"""Example: Health check reporting and rollback triggers"""

from src.health_check import HealthReporter, HealthStatus
from datetime import datetime, timedelta


def example_health_reporting():
    """Example of health check reporting"""
    print("Health Check Reporting Example")
    print("=" * 50)
    
    # Initialize health reporter
    reporter = HealthReporter(
        device_id="device-12345",
        firmware_version="1.2.3",
        server_url="https://ota.example.com/api",
        max_boot_count=3,
        max_watchdog_resets=5
    )
    
    print(f"Device ID: {reporter.device_id}")
    print(f"Firmware version: {reporter.firmware_version}")
    
    # Report healthy status
    print("\n1. Reporting healthy status...")
    success = reporter.report_health(
        status=HealthStatus.OK,
        boot_count=1,
        watchdog_resets=0,
        can_connect_to_broker=True,
        can_send_heartbeat=True,
        memory_usage_percent=45.0,
        cpu_usage_percent=30.0
    )
    
    if success:
        print("✓ Health reported successfully")
    else:
        print("✗ Health report failed (server not available in demo)")
    
    # Get current metrics
    metrics = reporter.get_metrics()
    print("\nCurrent Health Metrics:")
    for key, value in metrics.items():
        print(f"  {key}: {value}")
    
    # Check if rollback needed
    should_rollback = reporter.should_rollback()
    print(f"\nShould rollback: {should_rollback}")


def example_health_failure_rollback():
    """Example of health failure triggering rollback"""
    print("\n\nHealth Failure and Rollback Example")
    print("=" * 50)
    
    reporter = HealthReporter(
        device_id="device-67890",
        firmware_version="1.2.3",
        server_url="https://ota.example.com/api",
        max_boot_count=3,
        max_watchdog_resets=5
    )
    
    # Simulate boot loop
    print("Simulating boot loop...")
    reporter.report_health(
        status=HealthStatus.FAILED,
        boot_count=4,  # Exceeds max_boot_count
        watchdog_resets=0,
        can_connect_to_broker=False,
        can_send_heartbeat=False
    )
    
    print(f"Boot count: {reporter.metrics.boot_count}")
    print(f"Max boot count: {reporter.max_boot_count}")
    
    # Check if rollback needed
    should_rollback = reporter.should_rollback()
    print(f"\nShould rollback: {should_rollback}")
    
    if should_rollback:
        print("Triggering rollback...")
        # In real implementation, this would send rollback command
        print("✓ Rollback triggered")
        print("Device will boot from previous partition")


def example_watchdog_reset_rollback():
    """Example of watchdog resets triggering rollback"""
    print("\n\nWatchdog Reset Rollback Example")
    print("=" * 50)
    
    reporter = HealthReporter(
        device_id="device-99999",
        firmware_version="1.2.3",
        server_url="https://ota.example.com/api",
        max_boot_count=3,
        max_watchdog_resets=5
    )
    
    # Simulate excessive watchdog resets
    print("Simulating excessive watchdog resets...")
    reporter.report_health(
        status=HealthStatus.FAILED,
        boot_count=1,
        watchdog_resets=6,  # Exceeds max_watchdog_resets
        can_connect_to_broker=True,
        can_send_heartbeat=True
    )
    
    print(f"Watchdog resets: {reporter.metrics.watchdog_resets}")
    print(f"Max watchdog resets: {reporter.max_watchdog_resets}")
    
    should_rollback = reporter.should_rollback()
    print(f"\nShould rollback: {should_rollback}")
    
    if should_rollback:
        print("✓ Rollback should be triggered")


def example_connectivity_failure_rollback():
    """Example of connectivity failure triggering rollback"""
    print("\n\nConnectivity Failure Rollback Example")
    print("=" * 50)
    
    reporter = HealthReporter(
        device_id="device-11111",
        firmware_version="1.2.3",
        server_url="https://ota.example.com/api",
        max_boot_count=3,
        max_watchdog_resets=5,
        rollback_timeout_seconds=300  # 5 minutes
    )
    
    # Simulate connectivity loss
    print("Simulating connectivity loss...")
    reporter.report_health(
        status=HealthStatus.DEGRADED,
        boot_count=1,
        watchdog_resets=0,
        can_connect_to_broker=False,
        can_send_heartbeat=False
    )
    
    # Set last heartbeat time to past (simulating long outage)
    reporter.metrics.last_heartbeat_time = datetime.now() - timedelta(seconds=400)
    
    print(f"Can connect to broker: {reporter.metrics.can_connect_to_broker}")
    print(f"Last heartbeat: {reporter.metrics.last_heartbeat_time}")
    
    should_rollback = reporter.should_rollback()
    print(f"\nShould rollback: {should_rollback}")
    
    if should_rollback:
        print("✓ Rollback should be triggered due to connectivity failure")


if __name__ == "__main__":
    example_health_reporting()
    example_health_failure_rollback()
    example_watchdog_reset_rollback()
    example_connectivity_failure_rollback()
    
    print("\n✓ All examples completed")

