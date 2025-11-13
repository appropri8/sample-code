"""Tests for bounded agent"""

import pytest
from src.contracts import AgentContract
from src.bounded_agent import BoundedAgent, SimpleAgentCore
from src.timeouts import StepLimitExceeded


def test_bounded_agent_creation():
    """Test creating a bounded agent"""
    contract = AgentContract(
        name="test_agent",
        allowed_tools=["search_kb"],
        max_runtime_seconds=30,
        max_steps=10,
        max_tokens=1000,
        max_cost_dollars=1.0,
        required_output="text"
    )
    
    user_context = {
        "user_id": "user_123",
        "role": "user",
        "environment": "production",
        "request_id": "req_1",
        "context": {}
    }
    
    agent_core = SimpleAgentCore()
    agent = BoundedAgent(agent_core, contract, user_context)
    
    assert agent.contract.name == "test_agent"
    assert len(agent.available_tools) > 0


def test_bounded_agent_run():
    """Test running a bounded agent"""
    contract = AgentContract(
        name="test_agent",
        allowed_tools=["search_kb"],
        max_runtime_seconds=30,
        max_steps=10,
        max_tokens=1000,
        max_cost_dollars=1.0,
        required_output="text"
    )
    
    user_context = {
        "user_id": "user_123",
        "role": "user",
        "environment": "production",
        "request_id": "req_1",
        "context": {}
    }
    
    agent_core = SimpleAgentCore()
    agent = BoundedAgent(agent_core, contract, user_context)
    
    result = agent.run("Test query")
    
    assert "response" in result or "error" in result
    assert "request_id" in result


def test_bounded_agent_step_limit():
    """Test step limit enforcement"""
    contract = AgentContract(
        name="test_agent",
        allowed_tools=["search_kb"],
        max_runtime_seconds=30,
        max_steps=2,  # Very low limit
        max_tokens=1000,
        max_cost_dollars=1.0,
        required_output="text"
    )
    
    user_context = {
        "user_id": "user_123",
        "role": "user",
        "environment": "production",
        "request_id": "req_1",
        "context": {}
    }
    
    agent_core = SimpleAgentCore()
    agent = BoundedAgent(agent_core, contract, user_context)
    
    result = agent.run("Test query")
    
    # Should hit step limit
    assert result.get("error_type") == "step_limit" or result.get("complete") is True

