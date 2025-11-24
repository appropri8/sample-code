"""Example: Staged rollout orchestration"""

from src.rollout_orchestrator import (
    RolloutOrchestrator,
    DeviceGroup,
    PauseConditions
)
from datetime import datetime


def example_basic_rollout():
    """Basic staged rollout example"""
    print("Staged Rollout Orchestration Example")
    print("=" * 50)
    
    # Initialize orchestrator
    orchestrator = RolloutOrchestrator()
    
    # Register devices
    print("Registering devices...")
    for i in range(100):
        if i < 5:
            group = DeviceGroup.CANARY
        elif i < 20:
            group = DeviceGroup.INTERNAL
        elif i < 40:
            group = DeviceGroup.PILOT
        else:
            group = DeviceGroup.GENERAL
        
        orchestrator.register_device(
            device_id=f"device-{i:05d}",
            group=group,
            current_version="1.2.2"
        )
    
    print(f"Registered {orchestrator.metrics['total_devices']} devices")
    
    # Create rollout plan
    print("\nCreating rollout plan...")
    plan = orchestrator.create_rollout_plan(
        firmware_version="1.2.3",
        target_groups=[
            DeviceGroup.CANARY,
            DeviceGroup.INTERNAL,
            DeviceGroup.PILOT,
            DeviceGroup.GENERAL
        ],
        batch_size_percentage=10,  # 10% per batch
        pause_conditions=PauseConditions(
            failure_rate_threshold=0.05,  # 5%
            rollback_rate_threshold=0.02,  # 2%
            health_check_failure_rate=0.15,  # 15%
            wait_time_seconds=2  # 2 seconds for demo
        ),
        maintenance_window_only=False  # Allow updates anytime for demo
    )
    
    print(f"Firmware version: {plan.firmware_version}")
    print(f"Target groups: {[g.value for g in plan.target_groups]}")
    print(f"Batch size: {plan.batch_size_percentage}%")
    
    # Execute rollout
    print("\nExecuting rollout...")
    success = orchestrator.execute_rollout(plan)
    
    if success:
        print("\n✓ Rollout completed successfully")
    else:
        print("\n⚠ Rollout paused (conditions met)")
    
    # Show metrics
    print("\nRollout Metrics:")
    metrics = orchestrator.get_metrics()
    for key, value in metrics.items():
        print(f"  {key}: {value}")
    
    # Show progress
    progress = orchestrator.get_rollout_progress()
    print("\nRollout Progress:")
    for key, value in progress.items():
        print(f"  {key}: {value}")


def example_rollout_with_pause():
    """Example of rollout that pauses due to high failure rate"""
    print("\n\nRollout with Pause Condition Example")
    print("=" * 50)
    
    orchestrator = RolloutOrchestrator()
    
    # Register devices
    for i in range(50):
        orchestrator.register_device(
            device_id=f"device-{i:05d}",
            group=DeviceGroup.CANARY if i < 10 else DeviceGroup.INTERNAL,
            current_version="1.2.2"
        )
    
    # Create plan with strict pause conditions
    plan = orchestrator.create_rollout_plan(
        firmware_version="1.2.3",
        target_groups=[DeviceGroup.CANARY, DeviceGroup.INTERNAL],
        batch_size_percentage=20,
        pause_conditions=PauseConditions(
            failure_rate_threshold=0.01,  # Very strict: 1%
            rollback_rate_threshold=0.01,
            health_check_failure_rate=0.05,
            wait_time_seconds=1
        )
    )
    
    print("Executing rollout with strict pause conditions...")
    success = orchestrator.execute_rollout(plan)
    
    if not success:
        print("✓ Rollout correctly paused due to conditions")
    
    metrics = orchestrator.get_metrics()
    print(f"\nFinal metrics:")
    print(f"  Updated: {metrics['updated_devices']}")
    print(f"  Rolled back: {metrics['rolled_back_devices']}")
    print(f"  Health failures: {metrics['health_check_failures']}")


if __name__ == "__main__":
    example_basic_rollout()
    example_rollout_with_pause()
    
    print("\n✓ All examples completed")

