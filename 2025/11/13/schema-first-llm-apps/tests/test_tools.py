"""Tests for tool execution."""

import pytest
from src.tools import (
    tool_execution_wrapper,
    GetUserInfoArgs,
    UpdateTicketStatusArgs,
    SendNotificationArgs,
    get_user_info,
    update_ticket_status,
    send_notification
)


def test_get_user_info_success():
    """Test successful get_user_info tool execution."""
    result = tool_execution_wrapper(
        "get_user_info",
        {"user_id": "user123"},
        get_user_info,
        GetUserInfoArgs
    )
    
    assert result["success"] is True
    assert "result" in result
    assert result["result"]["user_id"] == "user123"


def test_update_ticket_status_success():
    """Test successful update_ticket_status tool execution."""
    result = tool_execution_wrapper(
        "update_ticket_status",
        {"ticket_id": "TICKET-12345", "status": "resolved"},
        update_ticket_status,
        UpdateTicketStatusArgs
    )
    
    assert result["success"] is True
    assert result["result"]["ticket_id"] == "TICKET-12345"
    assert result["result"]["status"] == "resolved"


def test_update_ticket_status_invalid_id():
    """Test update_ticket_status with invalid ticket ID."""
    result = tool_execution_wrapper(
        "update_ticket_status",
        {"ticket_id": "INVALID-123", "status": "resolved"},
        update_ticket_status,
        UpdateTicketStatusArgs
    )
    
    assert result["success"] is False
    assert "error" in result
    assert "TICKET-" in result["error"]


def test_send_notification_success():
    """Test successful send_notification tool execution."""
    result = tool_execution_wrapper(
        "send_notification",
        {
            "user_id": "user123",
            "message": "Test message",
            "priority": "high"
        },
        send_notification,
        SendNotificationArgs
    )
    
    assert result["success"] is True
    assert result["result"]["user_id"] == "user123"
    assert result["result"]["message"] == "Test message"


def test_send_notification_message_too_long():
    """Test send_notification with message too long."""
    long_message = "x" * 501  # Exceeds 500 character limit
    
    result = tool_execution_wrapper(
        "send_notification",
        {
            "user_id": "user123",
            "message": long_message
        },
        send_notification,
        SendNotificationArgs
    )
    
    assert result["success"] is False
    assert "error" in result

