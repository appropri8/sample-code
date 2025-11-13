"""Tests for agent contracts"""

import pytest
from src.contracts import AgentContract


def test_contract_creation():
    """Test creating a contract"""
    contract = AgentContract(
        name="test_agent",
        allowed_tools=["tool1", "tool2"],
        max_runtime_seconds=30,
        max_steps=10,
        max_tokens=1000,
        max_cost_dollars=1.0,
        required_output="text"
    )
    
    assert contract.name == "test_agent"
    assert len(contract.allowed_tools) == 2


def test_contract_validate_tool():
    """Test tool validation"""
    contract = AgentContract(
        name="test_agent",
        allowed_tools=["tool1", "tool2"],
        max_runtime_seconds=30,
        max_steps=10,
        max_tokens=1000,
        max_cost_dollars=1.0,
        required_output="text"
    )
    
    assert contract.validate_tool("tool1") is True
    assert contract.validate_tool("tool2") is True
    assert contract.validate_tool("tool3") is False

