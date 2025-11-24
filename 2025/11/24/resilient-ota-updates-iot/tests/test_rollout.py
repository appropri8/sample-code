"""Tests for rollout orchestrator"""

import pytest
from src.rollout_orchestrator import (
    RolloutOrchestrator,
    DeviceGroup,
    DeviceState,
    PauseConditions
)


def test_rollout_orchestrator_initialization():
    """Test rollout orchestrator initialization"""
    orchestrator = RolloutOrchestrator()
    
    assert orchestrator.devices == {}
    assert orchestrator.rollout_plans == []
    assert orchestrator.active_rollout is None
    assert orchestrator.metrics["total_devices"] == 0


def test_register_device():
    """Test registering devices"""
    orchestrator = RolloutOrchestrator()
    
    orchestrator.register_device(
        device_id="device-1",
        group=DeviceGroup.CANARY,
        current_version="1.2.2"
    )
    
    assert len(orchestrator.devices) == 1
    assert orchestrator.metrics["total_devices"] == 1
    assert orchestrator.devices["device-1"].group == DeviceGroup.CANARY
    assert orchestrator.devices["device-1"].state == DeviceState.PENDING


def test_create_rollout_plan():
    """Test creating rollout plan"""
    orchestrator = RolloutOrchestrator()
    
    plan = orchestrator.create_rollout_plan(
        firmware_version="1.2.3",
        target_groups=[DeviceGroup.CANARY, DeviceGroup.INTERNAL],
        batch_size_percentage=10
    )
    
    assert plan.firmware_version == "1.2.3"
    assert len(plan.target_groups) == 2
    assert plan.batch_size_percentage == 10
    assert len(orchestrator.rollout_plans) == 1


def test_get_device_status():
    """Test getting device status"""
    orchestrator = RolloutOrchestrator()
    
    orchestrator.register_device(
        device_id="device-1",
        group=DeviceGroup.CANARY,
        current_version="1.2.2"
    )
    
    status = orchestrator.get_device_status("device-1")
    assert status is not None
    assert status.device_id == "device-1"
    
    status = orchestrator.get_device_status("device-nonexistent")
    assert status is None

