"""Tests for kill switch functionality."""

import pytest
import json
import tempfile
from pathlib import Path
from src.kill_switch import KillSwitch


def test_kill_switch_initialization():
    """Test kill switch initialization."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = f.name
    
    try:
        kill_switch = KillSwitch(temp_path)
        assert not kill_switch.is_killed("support-agent", "v1.3.3")
    finally:
        Path(temp_path).unlink(missing_ok=True)


def test_kill_and_unkill_version():
    """Test killing and unkilling a version."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = f.name
    
    try:
        kill_switch = KillSwitch(temp_path)
        
        # Kill version
        kill_switch.kill_version(
            agent_name="support-agent",
            version="v1.3.3",
            reason="Test kill"
        )
        assert kill_switch.is_killed("support-agent", "v1.3.3")
        
        # Unkill version
        kill_switch.unkill_version("support-agent", "v1.3.3")
        assert not kill_switch.is_killed("support-agent", "v1.3.3")
    finally:
        Path(temp_path).unlink(missing_ok=True)


def test_feature_specific_kill():
    """Test feature-specific kill switch."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = f.name
    
    try:
        kill_switch = KillSwitch(temp_path)
        
        # Kill for specific feature
        kill_switch.kill_version(
            agent_name="support-agent",
            version="v1.3.3",
            reason="Feature issue",
            feature="email"
        )
        
        assert kill_switch.is_killed("support-agent", "v1.3.3", feature="email")
        assert not kill_switch.is_killed("support-agent", "v1.3.3", feature="search")
    finally:
        Path(temp_path).unlink(missing_ok=True)
