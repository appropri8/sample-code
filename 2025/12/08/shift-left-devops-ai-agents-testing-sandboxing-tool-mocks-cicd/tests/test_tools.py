"""Tests for tools."""

import pytest
from src.tools import MockDatabaseTool, MockEmailTool, MockSearchTool, RealDatabaseTool


def test_mock_database_search():
    """Test mock database search."""
    tool = MockDatabaseTool()
    results = tool.search("user1")
    assert len(results) > 0
    assert any("user1" in str(r).lower() for r in results)


def test_mock_database_limit():
    """Test that limit is respected."""
    tool = MockDatabaseTool()
    results = tool.search("user", limit=2)
    assert len(results) <= 2


def test_mock_email_send():
    """Test mock email sending."""
    tool = MockEmailTool()
    result = tool.send_email("test@example.com", "Test", "Body")
    assert result["status"] == "sent"
    assert "message_id" in result
    assert len(tool.sent_emails) == 1


def test_mock_search():
    """Test mock search tool."""
    tool = MockSearchTool()
    results = tool.search("Python tutorials")
    assert len(results) == 2
    assert all("id" in r and "title" in r for r in results)


def test_real_database_tool_interface():
    """Test that real database tool implements interface."""
    tool = RealDatabaseTool("fake_connection_string")
    results = tool.search("test", limit=5)
    assert isinstance(results, list)
