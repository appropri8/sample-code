"""Tests for quality gates."""

import pytest
import yaml
import tempfile
from pathlib import Path
from src.quality_gates import QualityGateChecker, QualityGate


def test_quality_gate_threshold():
    """Test threshold quality gate."""
    gate = QualityGate({
        "name": "test_gate",
        "type": "threshold",
        "metric": "score",
        "threshold": 0.8,
        "operator": ">="
    })
    
    # Should pass
    passed, msg = gate.check({"score": 0.9})
    assert passed
    
    # Should fail
    passed, msg = gate.check({"score": 0.7})
    assert not passed


def test_quality_gate_test_suite():
    """Test test suite quality gate."""
    gate = QualityGate({
        "name": "test_suite_gate",
        "type": "test_suite",
        "test_suite": "tests",
        "min_pass_rate": 1.0
    })
    
    # Should pass
    passed, msg = gate.check({
        "tests": [
            {"name": "test1", "passed": True},
            {"name": "test2", "passed": True}
        ]
    })
    assert passed
    
    # Should fail
    passed, msg = gate.check({
        "tests": [
            {"name": "test1", "passed": True},
            {"name": "test2", "passed": False}
        ]
    })
    assert not passed


def test_quality_gate_checker():
    """Test quality gate checker."""
    gates_config = {
        "gates": [
            {
                "name": "score",
                "type": "threshold",
                "metric": "score",
                "threshold": 0.8,
                "operator": ">="
            }
        ]
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(gates_config, f)
        temp_path = f.name
    
    try:
        checker = QualityGateChecker(temp_path)
        
        # Should pass
        all_passed, messages = checker.check_all({"score": 0.9})
        assert all_passed
        
        # Should fail
        all_passed, messages = checker.check_all({"score": 0.7})
        assert not all_passed
    finally:
        Path(temp_path).unlink(missing_ok=True)
