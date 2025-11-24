"""Backend rollout orchestration for OTA updates"""

import time
from typing import Dict, List, Optional, Set
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta


class DeviceGroup(str, Enum):
    """Device groups for staged rollouts"""
    CANARY = "canary"
    INTERNAL = "internal"
    PILOT = "pilot"
    GENERAL = "general"


class DeviceState(str, Enum):
    """Device update state"""
    PENDING = "pending"
    DOWNLOADING = "downloading"
    DOWNLOADED = "downloaded"
    INSTALLED = "installed"
    REBOOTED = "rebooted"
    HEALTH_OK = "health_ok"
    HEALTH_FAILED = "health_failed"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"


@dataclass
class PauseConditions:
    """Conditions that pause rollout"""
    failure_rate_threshold: float = 0.01  # 1%
    rollback_rate_threshold: float = 0.01  # 1%
    health_check_failure_rate: float = 0.10  # 10%
    min_devices_in_batch: int = 10
    wait_time_seconds: int = 300  # 5 minutes


@dataclass
class RolloutPlan:
    """Rollout plan configuration"""
    firmware_version: str
    target_groups: List[DeviceGroup]
    batch_size_percentage: int = 5  # 5% per batch
    pause_conditions: PauseConditions = field(default_factory=PauseConditions)
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None
    maintenance_window_only: bool = True


@dataclass
class DeviceStatus:
    """Status of a device in rollout"""
    device_id: str
    group: DeviceGroup
    state: DeviceState
    firmware_version: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None


class RolloutOrchestrator:
    """Orchestrates staged firmware rollouts"""
    
    def __init__(self):
        """Initialize rollout orchestrator"""
        self.devices: Dict[str, DeviceStatus] = {}
        self.rollout_plans: List[RolloutPlan] = []
        self.active_rollout: Optional[RolloutPlan] = None
        self.metrics: Dict[str, any] = {
            "total_devices": 0,
            "updated_devices": 0,
            "failed_devices": 0,
            "rolled_back_devices": 0,
            "health_check_failures": 0
        }
    
    def register_device(
        self,
        device_id: str,
        group: DeviceGroup,
        current_version: str
    ) -> None:
        """Register a device for rollout"""
        self.devices[device_id] = DeviceStatus(
            device_id=device_id,
            group=group,
            state=DeviceState.PENDING,
            firmware_version=current_version
        )
        self.metrics["total_devices"] += 1
    
    def create_rollout_plan(
        self,
        firmware_version: str,
        target_groups: List[DeviceGroup],
        batch_size_percentage: int = 5,
        pause_conditions: Optional[PauseConditions] = None,
        scheduled_start: Optional[datetime] = None,
        scheduled_end: Optional[datetime] = None,
        maintenance_window_only: bool = True
    ) -> RolloutPlan:
        """
        Create a rollout plan
        
        Args:
            firmware_version: Version to roll out
            target_groups: Device groups to target (in order)
            batch_size_percentage: Percentage of devices per batch
            pause_conditions: Conditions that pause rollout
            scheduled_start: When to start rollout
            scheduled_end: When to end rollout
            maintenance_window_only: Only update during maintenance windows
            
        Returns:
            Rollout plan
        """
        plan = RolloutPlan(
            firmware_version=firmware_version,
            target_groups=target_groups,
            batch_size_percentage=batch_size_percentage,
            pause_conditions=pause_conditions or PauseConditions(),
            scheduled_start=scheduled_start,
            scheduled_end=scheduled_end,
            maintenance_window_only=maintenance_window_only
        )
        self.rollout_plans.append(plan)
        return plan
    
    def execute_rollout(self, plan: RolloutPlan) -> bool:
        """
        Execute a rollout plan
        
        Args:
            plan: Rollout plan to execute
            
        Returns:
            True if rollout completed successfully, False if paused/failed
        """
        self.active_rollout = plan
        
        # Check if we're in maintenance window
        if plan.maintenance_window_only and not self._is_maintenance_window():
            print("Not in maintenance window, waiting...")
            return False
        
        # Execute rollout for each group in order
        for group in plan.target_groups:
            if not self._execute_group_rollout(plan, group):
                print(f"Rollout paused at group {group.value}")
                return False
        
        print("Rollout completed successfully")
        return True
    
    def _execute_group_rollout(self, plan: RolloutPlan, group: DeviceGroup) -> bool:
        """Execute rollout for a specific device group"""
        group_devices = [
            d for d in self.devices.values()
            if d.group == group and d.state == DeviceState.PENDING
        ]
        
        if not group_devices:
            print(f"No devices in group {group.value}")
            return True
        
        total_in_group = len(group_devices)
        batch_size = max(
            plan.pause_conditions.min_devices_in_batch,
            int(total_in_group * plan.batch_size_percentage / 100)
        )
        
        print(f"Rolling out to {total_in_group} devices in group {group.value} (batch size: {batch_size})")
        
        # Process devices in batches
        for i in range(0, total_in_group, batch_size):
            batch = group_devices[i:i + batch_size]
            
            # Update batch
            for device in batch:
                self._update_device(device, plan.firmware_version)
            
            # Wait and observe
            print(f"Waiting {plan.pause_conditions.wait_time_seconds}s to observe batch results...")
            time.sleep(plan.pause_conditions.wait_time_seconds)
            
            # Check pause conditions
            if self._should_pause_rollout(plan):
                print("Pause conditions met, stopping rollout")
                return False
        
        return True
    
    def _update_device(self, device: DeviceStatus, firmware_version: str) -> None:
        """Update a device (simulated)"""
        device.state = DeviceState.DOWNLOADING
        device.started_at = datetime.now()
        
        # Simulate update process
        # In real implementation, this would send update command to device
        time.sleep(0.1)  # Simulate download
        
        device.state = DeviceState.DOWNLOADED
        time.sleep(0.1)  # Simulate install
        
        device.state = DeviceState.INSTALLED
        time.sleep(0.1)  # Simulate reboot
        
        device.state = DeviceState.REBOOTED
        
        # Simulate health check (90% success rate)
        import random
        if random.random() < 0.9:
            device.state = DeviceState.HEALTH_OK
            device.completed_at = datetime.now()
            self.metrics["updated_devices"] += 1
        else:
            device.state = DeviceState.HEALTH_FAILED
            self.metrics["health_check_failures"] += 1
            self._rollback_device(device)
    
    def _rollback_device(self, device: DeviceStatus) -> None:
        """Roll back a device"""
        device.state = DeviceState.ROLLED_BACK
        self.metrics["rolled_back_devices"] += 1
        print(f"Device {device.device_id} rolled back")
    
    def _should_pause_rollout(self, plan: RolloutPlan) -> bool:
        """Check if rollout should be paused"""
        conditions = plan.pause_conditions
        
        # Calculate failure rate
        total_attempted = sum(
            1 for d in self.devices.values()
            if d.started_at is not None
        )
        
        if total_attempted == 0:
            return False
        
        failed_count = sum(
            1 for d in self.devices.values()
            if d.state in [DeviceState.FAILED, DeviceState.HEALTH_FAILED]
        )
        failure_rate = failed_count / total_attempted if total_attempted > 0 else 0
        
        # Calculate rollback rate
        rolled_back_count = sum(
            1 for d in self.devices.values()
            if d.state == DeviceState.ROLLED_BACK
        )
        rollback_rate = rolled_back_count / total_attempted if total_attempted > 0 else 0
        
        # Calculate health check failure rate
        health_checked = sum(
            1 for d in self.devices.values()
            if d.state in [DeviceState.HEALTH_OK, DeviceState.HEALTH_FAILED]
        )
        health_failure_rate = (
            self.metrics["health_check_failures"] / health_checked
            if health_checked > 0 else 0
        )
        
        # Check conditions
        if failure_rate > conditions.failure_rate_threshold:
            print(f"Failure rate {failure_rate:.2%} exceeds threshold {conditions.failure_rate_threshold:.2%}")
            return True
        
        if rollback_rate > conditions.rollback_rate_threshold:
            print(f"Rollback rate {rollback_rate:.2%} exceeds threshold {conditions.rollback_rate_threshold:.2%}")
            return True
        
        if health_failure_rate > conditions.health_check_failure_rate:
            print(f"Health failure rate {health_failure_rate:.2%} exceeds threshold {conditions.health_check_failure_rate:.2%}")
            return True
        
        return False
    
    def _is_maintenance_window(self) -> bool:
        """Check if current time is in maintenance window"""
        now = datetime.now()
        # Maintenance window: 2 AM - 4 AM
        return 2 <= now.hour < 4
    
    def get_metrics(self) -> Dict[str, any]:
        """Get rollout metrics"""
        return self.metrics.copy()
    
    def get_device_status(self, device_id: str) -> Optional[DeviceStatus]:
        """Get status of a specific device"""
        return self.devices.get(device_id)
    
    def get_rollout_progress(self) -> Dict[str, any]:
        """Get current rollout progress"""
        if not self.active_rollout:
            return {"status": "no_active_rollout"}
        
        total = self.metrics["total_devices"]
        updated = self.metrics["updated_devices"]
        failed = self.metrics["failed_devices"]
        rolled_back = self.metrics["rolled_back_devices"]
        
        return {
            "firmware_version": self.active_rollout.firmware_version,
            "total_devices": total,
            "updated": updated,
            "failed": failed,
            "rolled_back": rolled_back,
            "progress_percentage": (updated / total * 100) if total > 0 else 0,
            "failure_rate": (failed / total) if total > 0 else 0,
            "rollback_rate": (rolled_back / total) if total > 0 else 0
        }

