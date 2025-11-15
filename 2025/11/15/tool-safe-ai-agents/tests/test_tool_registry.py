"""Tests for tool registry"""

import pytest
from src.tool_registry import (
    get_tool,
    get_tools_for_role,
    is_tool_allowed,
    disable_tool,
    enable_tool,
    TOOL_REGISTRY
)


def test_get_tool():
    """Test getting a tool from registry"""
    tool = get_tool("read_ticket")
    assert tool is not None
    assert tool.name == "read_ticket"
    
    tool = get_tool("nonexistent")
    assert tool is None


def test_get_tools_for_role():
    """Test getting tools for a role"""
    tools = get_tools_for_role("support_agent")
    assert len(tools) > 0
    assert any(tool.name == "read_ticket" for tool in tools)
    assert any(tool.name == "add_comment" for tool in tools)
    
    tools = get_tools_for_role("readonly")
    assert len(tools) > 0
    assert any(tool.name == "read_ticket" for tool in tools)
    # readonly should not have add_comment
    assert not any(tool.name == "add_comment" for tool in tools)


def test_is_tool_allowed():
    """Test checking if tool is allowed for role"""
    assert is_tool_allowed("read_ticket", "support_agent") is True
    assert is_tool_allowed("close_ticket", "support_agent") is False
    assert is_tool_allowed("close_ticket", "support_manager") is True
    assert is_tool_allowed("nonexistent", "support_agent") is False


def test_disable_tool():
    """Test disabling a tool"""
    tool = get_tool("read_ticket")
    assert tool.enabled is True
    
    disable_tool("read_ticket")
    tool = get_tool("read_ticket")
    assert tool.enabled is False
    
    # Re-enable for other tests
    enable_tool("read_ticket")
    tool = get_tool("read_ticket")
    assert tool.enabled is True


def test_tool_metadata():
    """Test tool metadata"""
    tool = get_tool("close_ticket")
    assert tool.requires_approval is True
    assert tool.risk_level.value == "high"
    assert "support_manager" in tool.allowed_roles

