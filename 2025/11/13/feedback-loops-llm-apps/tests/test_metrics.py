"""Tests for metrics calculation"""

import pytest
from src.metrics import (
    calculate_task_success_rate,
    calculate_human_help_rate,
    calculate_safety_trigger_rate,
    calculate_latency_percentiles,
    calculate_cost_per_success,
    compare_prompt_versions
)


def test_calculate_task_success_rate():
    """Test task success rate calculation."""
    feedback_data = [
        {"feedback_value": {"task_succeeded": True}},
        {"feedback_value": {"task_succeeded": False}},
        {"feedback_value": {"task_succeeded": True}},
    ]
    
    rate = calculate_task_success_rate(feedback_data)
    assert rate == pytest.approx(2/3, 0.01)


def test_calculate_human_help_rate():
    """Test human help rate calculation."""
    feedback_data = [
        {"feedback_value": {"needed_human_help": True}},
        {"feedback_value": {"needed_human_help": False}},
        {"feedback_value": {"needed_human_help": False}},
    ]
    
    rate = calculate_human_help_rate(feedback_data)
    assert rate == pytest.approx(1/3, 0.01)


def test_calculate_safety_trigger_rate():
    """Test safety trigger rate calculation."""
    feedback_data = [
        {"feedback_value": {"safety_filter_level": "high"}},
        {"feedback_value": {"safety_filter_level": "medium"}},
        {"feedback_value": {"safety_filter_level": "low"}},
        {"feedback_value": {}},
    ]
    
    rates = calculate_safety_trigger_rate(feedback_data)
    assert rates["high"] == pytest.approx(0.25, 0.01)
    assert rates["medium"] == pytest.approx(0.25, 0.01)
    assert rates["low"] == pytest.approx(0.25, 0.01)


def test_calculate_latency_percentiles():
    """Test latency percentile calculation."""
    feedback_data = [
        {"metadata": {"latency_ms": 100}},
        {"metadata": {"latency_ms": 200}},
        {"metadata": {"latency_ms": 300}},
        {"metadata": {"latency_ms": 400}},
        {"metadata": {"latency_ms": 500}},
    ]
    
    percentiles = calculate_latency_percentiles(feedback_data)
    assert "p50" in percentiles
    assert "p95" in percentiles
    assert "p99" in percentiles


def test_calculate_cost_per_success():
    """Test cost per success calculation."""
    feedback_data = [
        {
            "feedback_value": {"task_succeeded": True},
            "metadata": {"cost_estimate": 0.01}
        },
        {
            "feedback_value": {"task_succeeded": False},
            "metadata": {"cost_estimate": 0.02}
        },
        {
            "feedback_value": {"task_succeeded": True},
            "metadata": {"cost_estimate": 0.01}
        },
    ]
    
    cost = calculate_cost_per_success(feedback_data)
    assert cost == pytest.approx(0.01, 0.001)


def test_compare_prompt_versions():
    """Test comparing prompt versions."""
    feedback_data = [
        {
            "prompt_version": "v1",
            "feedback_value": {"task_succeeded": True},
            "metadata": {"latency_ms": 100, "cost_estimate": 0.01}
        },
        {
            "prompt_version": "v1",
            "feedback_value": {"task_succeeded": False},
            "metadata": {"latency_ms": 200, "cost_estimate": 0.02}
        },
        {
            "prompt_version": "v2",
            "feedback_value": {"task_succeeded": True},
            "metadata": {"latency_ms": 150, "cost_estimate": 0.015}
        },
    ]
    
    comparison = compare_prompt_versions(feedback_data)
    
    assert "v1" in comparison
    assert "v2" in comparison
    assert comparison["v1"]["sample_size"] == 2
    assert comparison["v2"]["sample_size"] == 1

