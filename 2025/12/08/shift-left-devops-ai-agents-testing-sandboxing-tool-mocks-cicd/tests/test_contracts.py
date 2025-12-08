"""Tests for contract validation."""

import pytest
from src.contract_validator import validate_agent_action, check_policy_violations


def test_valid_action():
    """Test that a valid action passes validation."""
    action = {
        "tool_name": "search_database",
        "parameters": {"query": "find users", "limit": 10}
    }
    is_valid, errors = validate_agent_action(action)
    assert is_valid
    assert len(errors) == 0


def test_invalid_tool_name():
    """Test that invalid tool name fails validation."""
    action = {
        "tool_name": "invalid_tool",
        "parameters": {"query": "test"}
    }
    is_valid, errors = validate_agent_action(action)
    assert not is_valid
    assert len(errors) > 0


def test_missing_required_parameter():
    """Test that missing required parameter fails validation."""
    action = {
        "tool_name": "search_database",
        "parameters": {}  # Missing 'query'
    }
    is_valid, errors = validate_agent_action(action)
    assert not is_valid
    assert "query" in str(errors[0]).lower()


def test_forbidden_tool_in_test():
    """Test that forbidden tools are caught."""
    action = {
        "tool_name": "/delete_user",
        "parameters": {"query": "test"}
    }
    is_valid, errors = validate_agent_action(action)
    assert not is_valid
    assert "forbidden" in str(errors[0]).lower()


def test_policy_max_steps():
    """Test that exceeding max steps is caught."""
    actions = [
        {"tool_name": "search_database", "parameters": {"query": f"query_{i}"}}
        for i in range(15)  # More than max_steps (10)
    ]
    violations = check_policy_violations(actions, environment="test")
    assert len(violations) > 0
    assert "max steps" in violations[0].lower()
