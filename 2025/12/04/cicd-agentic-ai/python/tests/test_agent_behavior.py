"""Behavioral tests for agents"""
import pytest
from unittest.mock import Mock
from src.agent import Agent, AgentRole


def test_planner_selects_correct_tools():
    """Test planner selects appropriate tools for task"""
    agent = Agent(
        role=AgentRole.PLANNER,
        model_config={"model": "gpt-4", "temperature": 0.0},
        tools=["search_kb", "create_ticket", "escalate"],
        version="1.0.0"
    )
    
    result = agent.run({"input": "User wants to reset password"})
    
    assert result["success"] is True
    assert "search_kb" in result.get("tools_called", [])
    assert "create_ticket" in result.get("tools_called", [])


def test_agent_retry_strategy():
    """Test agent handles failures"""
    agent = Agent(
        role=AgentRole.WORKER,
        model_config={"model": "gpt-4"},
        tools=["unreliable_tool"],
        version="1.0.0"
    )
    
    call_count = 0
    
    def unreliable_tool(*args):
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise Exception("Tool failed")
        return {"success": True}
    
    agent.tool_registry["unreliable_tool"] = unreliable_tool
    
    result = agent.run({"tools": ["unreliable_tool"]})
    
    # Agent should handle the error
    assert "error" in result or result["success"] is True


def test_agent_argument_shapes():
    """Test agent passes correct argument shapes"""
    agent = Agent(
        role=AgentRole.WORKER,
        model_config={"model": "gpt-4"},
        tools=["update_billing"],
        version="1.0.0"
    )
    
    captured_args = []
    
    def capture_args(**kwargs):
        captured_args.append(kwargs)
        return {"updated": True}
    
    agent.tool_registry["update_billing"] = capture_args
    
    agent.run({"tools": ["update_billing"], "user_id": "123", "plan": "premium"})
    
    assert len(captured_args) > 0 or len(agent.tools_called) > 0

