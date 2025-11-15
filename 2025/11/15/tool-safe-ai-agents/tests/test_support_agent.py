"""Tests for support agent"""

import pytest
from src.support_agent import SupportAgent


def test_get_available_tools():
    """Test getting available tools"""
    agent = SupportAgent(user_role="support_agent", user_id="test_agent")
    tools = agent.get_available_tools()
    
    assert "read_ticket" in tools
    assert "add_comment" in tools
    assert "close_ticket" not in tools  # support_agent can't close
    
    manager = SupportAgent(user_role="support_manager", user_id="test_manager")
    manager_tools = manager.get_available_tools()
    assert "close_ticket" in manager_tools


def test_handle_user_request():
    """Test handling user requests"""
    agent = SupportAgent(user_role="support_agent", user_id="test_agent")
    
    # Read ticket
    result = agent.handle_user_request("read ticket TKT-12345")
    assert result["status"] == "success"
    
    # Add comment
    result = agent.handle_user_request("add comment to TKT-12345: Test comment")
    assert result["status"] == "success"
    
    # Try to close (should fail for support_agent)
    result = agent.handle_user_request("close ticket TKT-12345")
    assert result["status"] == "error" or result.get("status") == "approval_required"


def test_approval_flow():
    """Test approval flow through agent"""
    manager = SupportAgent(user_role="support_manager", user_id="test_manager")
    
    # Request to close ticket
    result = manager.handle_user_request("close ticket TKT-12345 reason: Resolved")
    
    if result.get("status") == "approval_required":
        approval_id = result.get("approval_id")
        
        # Approve
        approval_result = manager.approve_action(approval_id, "reviewer_001")
        assert approval_result["status"] == "success"

