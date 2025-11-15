"""Tests for policy layer"""

import pytest
from src.policy_layer import PolicyLayer


def test_permission_check():
    """Test that policy layer checks permissions"""
    policy = PolicyLayer(user_role="support_agent", user_id="test_user")
    
    # Should be allowed
    result = policy.call_tool_with_policy(
        tool_name="read_ticket",
        args={"ticket_id": "TKT-123"},
        run_id="test_001"
    )
    assert result["status"] == "success"
    
    # Should be blocked (support_agent can't close tickets)
    result = policy.call_tool_with_policy(
        tool_name="close_ticket",
        args={"ticket_id": "TKT-123", "reason": "Test"},
        run_id="test_002"
    )
    assert result["status"] == "error"
    assert "not allowed" in result["error"].lower()


def test_validation():
    """Test that policy layer validates inputs"""
    policy = PolicyLayer(user_role="support_agent", user_id="test_user")
    
    # Missing required field
    result = policy.call_tool_with_policy(
        tool_name="add_comment",
        args={"ticket_id": "TKT-123"},  # Missing 'comment'
        run_id="test_003"
    )
    assert result["status"] == "error"
    assert "validation" in result["error"].lower() or "required" in result["error"].lower()


def test_approval_required():
    """Test that high-risk tools require approval"""
    policy = PolicyLayer(user_role="support_manager", user_id="manager_test")
    
    # Should require approval
    result = policy.call_tool_with_policy(
        tool_name="close_ticket",
        args={"ticket_id": "TKT-123", "reason": "Resolved"},
        run_id="test_004"
    )
    assert result["status"] == "approval_required"
    assert "approval_id" in result


def test_approval_flow():
    """Test the approval flow"""
    policy = PolicyLayer(user_role="support_manager", user_id="manager_test")
    
    # Request approval
    result = policy.call_tool_with_policy(
        tool_name="close_ticket",
        args={"ticket_id": "TKT-123", "reason": "Resolved"},
        run_id="test_005"
    )
    assert result["status"] == "approval_required"
    approval_id = result["approval_id"]
    
    # Approve
    approval_result = policy.approve_action(approval_id, "reviewer_001")
    assert approval_result["status"] == "success"
    
    # Check that approval is no longer pending
    pending = policy.get_pending_approvals()
    assert not any(a.approval_id == approval_id and a.status == "pending" for a in pending)


def test_nonexistent_tool():
    """Test handling of nonexistent tools"""
    policy = PolicyLayer(user_role="support_agent", user_id="test_user")
    
    result = policy.call_tool_with_policy(
        tool_name="nonexistent_tool",
        args={},
        run_id="test_006"
    )
    assert result["status"] == "error"
    assert "not found" in result["error"].lower()

