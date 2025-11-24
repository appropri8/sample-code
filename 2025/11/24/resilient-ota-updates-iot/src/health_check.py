"""Health check reporting and rollback triggers for OTA updates"""

import time
import requests
from typing import Optional, Dict, Any
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta


class HealthStatus(str, Enum):
    """Device health status"""
    OK = "ok"
    DEGRADED = "degraded"
    FAILED = "failed"
    UNKNOWN = "unknown"


@dataclass
class HealthMetrics:
    """Device health metrics"""
    boot_count: int = 0
    watchdog_resets: int = 0
    can_connect_to_broker: bool = False
    can_send_heartbeat: bool = False
    last_heartbeat_time: Optional[datetime] = None
    memory_usage_percent: Optional[float] = None
    cpu_usage_percent: Optional[float] = None


class HealthReporter:
    """Reports device health and triggers rollbacks"""
    
    def __init__(
        self,
        device_id: str,
        firmware_version: str,
        server_url: str,
        max_boot_count: int = 3,
        max_watchdog_resets: int = 5,
        health_check_interval_seconds: int = 60,
        rollback_timeout_seconds: int = 300  # 5 minutes
    ):
        """
        Initialize health reporter
        
        Args:
            device_id: Unique device identifier
            firmware_version: Current firmware version
            server_url: URL of health reporting server
            max_boot_count: Maximum boot count before rollback
            max_watchdog_resets: Maximum watchdog resets before rollback
            health_check_interval_seconds: How often to check health
            rollback_timeout_seconds: Timeout for health checks before rollback
        """
        self.device_id = device_id
        self.firmware_version = firmware_version
        self.server_url = server_url
        self.max_boot_count = max_boot_count
        self.max_watchdog_resets = max_watchdog_resets
        self.health_check_interval = health_check_interval_seconds
        self.rollback_timeout = rollback_timeout_seconds
        
        self.metrics = HealthMetrics()
        self.last_update_time: Optional[datetime] = None
        self.health_history: list[tuple[datetime, HealthStatus]] = []
    
    def report_health(
        self,
        status: HealthStatus,
        boot_count: Optional[int] = None,
        watchdog_resets: Optional[int] = None,
        can_connect_to_broker: Optional[bool] = None,
        can_send_heartbeat: Optional[bool] = None,
        memory_usage_percent: Optional[float] = None,
        cpu_usage_percent: Optional[float] = None
    ) -> bool:
        """
        Report device health to server
        
        Args:
            status: Overall health status
            boot_count: Number of boots since last update
            watchdog_resets: Number of watchdog resets
            can_connect_to_broker: Can device connect to message broker
            can_send_heartbeat: Can device send heartbeat
            memory_usage_percent: Memory usage percentage
            cpu_usage_percent: CPU usage percentage
            
        Returns:
            True if report successful, False otherwise
        """
        now = datetime.now()
        
        # Update metrics
        if boot_count is not None:
            self.metrics.boot_count = boot_count
        if watchdog_resets is not None:
            self.metrics.watchdog_resets = watchdog_resets
        if can_connect_to_broker is not None:
            self.metrics.can_connect_to_broker = can_connect_to_broker
        if can_send_heartbeat is not None:
            self.metrics.can_send_heartbeat = can_send_heartbeat
            if can_send_heartbeat:
                self.metrics.last_heartbeat_time = now
        if memory_usage_percent is not None:
            self.metrics.memory_usage_percent = memory_usage_percent
        if cpu_usage_percent is not None:
            self.metrics.cpu_usage_percent = cpu_usage_percent
        
        # Record health history
        self.health_history.append((now, status))
        # Keep only last 100 entries
        if len(self.health_history) > 100:
            self.health_history.pop(0)
        
        # Prepare payload
        payload = {
            "device_id": self.device_id,
            "firmware_version": self.firmware_version,
            "status": status.value,
            "timestamp": now.isoformat(),
            "metrics": {
                "boot_count": self.metrics.boot_count,
                "watchdog_resets": self.metrics.watchdog_resets,
                "can_connect_to_broker": self.metrics.can_connect_to_broker,
                "can_send_heartbeat": self.metrics.can_send_heartbeat,
                "last_heartbeat_time": (
                    self.metrics.last_heartbeat_time.isoformat()
                    if self.metrics.last_heartbeat_time else None
                ),
                "memory_usage_percent": self.metrics.memory_usage_percent,
                "cpu_usage_percent": self.metrics.cpu_usage_percent
            }
        }
        
        # Send to server
        try:
            response = requests.post(
                f"{self.server_url}/health",
                json=payload,
                timeout=5
            )
            response.raise_for_status()
            self.last_update_time = now
            return True
        except Exception as e:
            print(f"Error reporting health: {e}")
            return False
    
    def should_rollback(self) -> bool:
        """
        Determine if device should roll back based on health metrics
        
        Returns:
            True if rollback should be triggered, False otherwise
        """
        # Check boot count
        if self.metrics.boot_count > self.max_boot_count:
            print(f"Boot count {self.metrics.boot_count} exceeds threshold {self.max_boot_count}")
            return True
        
        # Check watchdog resets
        if self.metrics.watchdog_resets > self.max_watchdog_resets:
            print(f"Watchdog resets {self.metrics.watchdog_resets} exceeds threshold {self.max_watchdog_resets}")
            return True
        
        # Check connectivity
        if not self.metrics.can_connect_to_broker:
            # Check if this has been failing for too long
            if self.metrics.last_heartbeat_time:
                time_since_heartbeat = datetime.now() - self.metrics.last_heartbeat_time
                if time_since_heartbeat.total_seconds() > self.rollback_timeout:
                    print(f"Broker connectivity failed for {time_since_heartbeat.total_seconds()}s")
                    return True
        
        # Check recent health history
        if len(self.health_history) >= 3:
            recent_statuses = [status for _, status in self.health_history[-3:]]
            if all(s == HealthStatus.FAILED for s in recent_statuses):
                print("Health check failed 3 times in a row")
                return True
        
        return False
    
    def trigger_rollback(self) -> bool:
        """
        Trigger device rollback
        
        Returns:
            True if rollback triggered successfully, False otherwise
        """
        payload = {
            "device_id": self.device_id,
            "firmware_version": self.firmware_version,
            "reason": "health_check_failed",
            "timestamp": datetime.now().isoformat(),
            "metrics": {
                "boot_count": self.metrics.boot_count,
                "watchdog_resets": self.metrics.watchdog_resets,
                "can_connect_to_broker": self.metrics.can_connect_to_broker,
                "can_send_heartbeat": self.metrics.can_send_heartbeat
            }
        }
        
        try:
            response = requests.post(
                f"{self.server_url}/rollback",
                json=payload,
                timeout=5
            )
            response.raise_for_status()
            print(f"Rollback triggered for device {self.device_id}")
            return True
        except Exception as e:
            print(f"Error triggering rollback: {e}")
            return False
    
    def get_health_status(self) -> HealthStatus:
        """Get current health status based on metrics"""
        if self.should_rollback():
            return HealthStatus.FAILED
        
        if not self.metrics.can_connect_to_broker or not self.metrics.can_send_heartbeat:
            return HealthStatus.DEGRADED
        
        if self.metrics.boot_count > 0 or self.metrics.watchdog_resets > 0:
            return HealthStatus.DEGRADED
        
        return HealthStatus.OK
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current health metrics"""
        return {
            "device_id": self.device_id,
            "firmware_version": self.firmware_version,
            "status": self.get_health_status().value,
            "boot_count": self.metrics.boot_count,
            "watchdog_resets": self.metrics.watchdog_resets,
            "can_connect_to_broker": self.metrics.can_connect_to_broker,
            "can_send_heartbeat": self.metrics.can_send_heartbeat,
            "last_heartbeat_time": (
                self.metrics.last_heartbeat_time.isoformat()
                if self.metrics.last_heartbeat_time else None
            ),
            "memory_usage_percent": self.metrics.memory_usage_percent,
            "cpu_usage_percent": self.metrics.cpu_usage_percent
        }

