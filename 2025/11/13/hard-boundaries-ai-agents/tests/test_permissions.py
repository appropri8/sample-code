"""Tests for permissions"""

from src.permissions import (
    get_tools_for_role,
    get_tools_for_env,
    can_call_tool,
    get_tools_for_context
)


def test_role_permissions():
    """Test role-based permissions"""
    user_tools = get_tools_for_role("user")
    admin_tools = get_tools_for_role("admin")
    readonly_tools = get_tools_for_role("readonly")
    
    assert "search_kb" in user_tools
    assert "delete_ticket" not in user_tools
    assert "delete_ticket" in admin_tools
    assert "create_ticket" not in readonly_tools


def test_env_permissions():
    """Test environment-based permissions"""
    prod_tools = get_tools_for_env("production")
    dev_tools = get_tools_for_env("development")
    
    assert "search_kb" in prod_tools
    assert "reset_database" not in prod_tools
    assert "reset_database" in dev_tools


def test_tool_matrix():
    """Test tool capability matrix"""
    assert can_call_tool("search_kb", "user", "production") is True
    assert can_call_tool("delete_ticket", "user", "production") is False
    assert can_call_tool("delete_ticket", "admin", "staging") is True
    assert can_call_tool("reset_database", "admin", "production") is False


def test_context_permissions():
    """Test context-based permissions"""
    tools = get_tools_for_context("user_1", "enterprise", "user", "production")
    
    assert "search_kb" in tools
    assert "advanced_analytics" in tools  # Enterprise feature

