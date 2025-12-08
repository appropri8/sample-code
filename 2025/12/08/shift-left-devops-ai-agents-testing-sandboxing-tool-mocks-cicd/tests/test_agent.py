"""Tests for agent with mocked LLM."""

import pytest
from unittest.mock import Mock, patch
from src.agent import Agent, create_agent
from src.tools import MockDatabaseTool, MockEmailTool, MockSearchTool


def test_agent_tool_selection():
    """Test that agent selects correct tool for search request."""
    tools = {
        "database": MockDatabaseTool(),
        "email": MockEmailTool(),
        "search": MockSearchTool()
    }
    agent = Agent(tools=tools)
    
    response = agent.process("Search for user1@example.com")
    
    assert len(response["tool_calls"]) > 0
    assert response["tool_calls"][0]["tool_name"] == "search_database"
    assert "user1" in str(response["tool_calls"][0]["parameters"]).lower()


def test_agent_with_mocks():
    """Test agent with mock tools."""
    agent = create_agent(use_mocks=True)
    response = agent.process("Find users with email")
    
    assert response["step_count"] > 0
    assert len(response["tool_calls"]) > 0
    assert response["errors"] == []


def test_agent_respects_max_steps():
    """Test that agent respects max steps limit."""
    agent = create_agent(use_mocks=True)
    # This is a simplified test - in real implementation would need
    # an agent that makes multiple tool calls
    response = agent.process("Search for something", max_steps=5)
    assert response["step_count"] <= 5


def test_agent_handles_invalid_action():
    """Test that agent handles invalid actions gracefully."""
    agent = create_agent(use_mocks=True)
    # In a real implementation, would test with an action that fails validation
    response = agent.process("Invalid request that causes error")
    # Should not crash, should return error in response
    assert "errors" in response or "final_message" in response
