"""Tests for policy: allowlist by role, forbidden fields, requires_approval."""

import pytest
from src.gateway.policy import allow_tool, has_forbidden_fields, requires_approval


def test_allow_tool_read_only_agent():
    assert allow_tool("read_only_agent", "read_file") is True
    assert allow_tool("read_only_agent", "search") is True
    assert allow_tool("read_only_agent", "write_file") is False
    assert allow_tool("read_only_agent", "delete_file") is False


def test_allow_tool_action_agent():
    assert allow_tool("action_agent", "read_file") is True
    assert allow_tool("action_agent", "write_file") is True
    assert allow_tool("action_agent", "delete_file") is True


def test_allow_tool_unknown_role():
    assert allow_tool("unknown_role", "read_file") is False


def test_has_forbidden_fields():
    assert has_forbidden_fields({"path": "/tmp/foo"}) == []
    assert "password" in str(has_forbidden_fields({"password": "secret"}))
    assert "api_key" in str(has_forbidden_fields({"api_key": "key123"}))


def test_requires_approval():
    assert requires_approval("read_file") is False
    assert requires_approval("search") is False
    assert requires_approval("write_file") is True
    assert requires_approval("delete_file") is True
