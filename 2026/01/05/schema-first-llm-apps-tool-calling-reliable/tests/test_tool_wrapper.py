"""Tests for tool execution wrapper."""

import pytest
from src.tool_wrapper import (
    tool_execution_wrapper,
    ALLOWED_TOOLS,
    get_user_info,
    update_ticket,
    send_notification,
)
from src.schemas import GetUserInfoArgs, UpdateTicketArgs, SendNotificationArgs


class TestToolWrapper:
    """Test tool execution wrapper."""
    
    def test_tool_wrapper_success(self):
        """Test successful tool execution."""
        result = tool_execution_wrapper(
            "get_user_info",
            {"user_id": "user_123"},
            get_user_info,
            GetUserInfoArgs
        )
        
        assert result["success"] is True
        assert "result" in result
        assert result["result"]["user_id"] == "user_123"
    
    def test_tool_wrapper_validation_error(self):
        """Test tool wrapper catches validation errors."""
        result = tool_execution_wrapper(
            "get_user_info",
            {"user_id": "invalid"},  # Doesn't start with 'user_'
            get_user_info,
            GetUserInfoArgs
        )
        
        assert result["success"] is False
        assert "error" in result
        assert "user_id" in result["error"].lower()
    
    def test_tool_wrapper_not_in_allowlist(self):
        """Test tool wrapper rejects tools not in allowlist."""
        def malicious_tool():
            return "hacked"
        
        result = tool_execution_wrapper(
            "malicious_tool",  # Not in ALLOWED_TOOLS
            {},
            malicious_tool
        )
        
        assert result["success"] is False
        assert "not allowed" in result["error"].lower()
    
    def test_tool_wrapper_update_ticket(self):
        """Test updating ticket status."""
        result = tool_execution_wrapper(
            "update_ticket",
            {"ticket_id": "TICKET-123", "status": "resolved"},
            update_ticket,
            UpdateTicketArgs
        )
        
        assert result["success"] is True
        assert result["result"]["status"] == "resolved"
    
    def test_tool_wrapper_send_notification(self):
        """Test sending notification."""
        result = tool_execution_wrapper(
            "send_notification",
            {
                "user_id": "user_123",
                "message": "Test notification",
                "priority": "high"
            },
            send_notification,
            SendNotificationArgs
        )
        
        assert result["success"] is True
        assert result["result"]["priority"] == "high"
    
    def test_tool_wrapper_message_too_long(self):
        """Test validation fails for message too long."""
        long_message = "x" * 501  # Over 500 char limit
        
        result = tool_execution_wrapper(
            "send_notification",
            {
                "user_id": "user_123",
                "message": long_message
            },
            send_notification,
            SendNotificationArgs
        )
        
        assert result["success"] is False
        assert "message" in result["error"].lower()
        assert "500" in result["error"]
    
    def test_tool_wrapper_uses_allowlist_validator(self):
        """Test tool wrapper uses validator from allowlist if not provided."""
        result = tool_execution_wrapper(
            "get_user_info",
            {"user_id": "user_123"},
            get_user_info
            # No validator provided, should use ALLOWED_TOOLS["get_user_info"]
        )
        
        assert result["success"] is True
        assert result["result"]["user_id"] == "user_123"
    
    def test_tool_wrapper_execution_exception(self):
        """Test tool wrapper handles execution exceptions."""
        def failing_tool(user_id: str):
            raise RuntimeError("Database connection failed")
        
        result = tool_execution_wrapper(
            "get_user_info",
            {"user_id": "user_123"},
            failing_tool,
            GetUserInfoArgs
        )
        
        assert result["success"] is False
        assert "execution failed" in result["error"].lower()
