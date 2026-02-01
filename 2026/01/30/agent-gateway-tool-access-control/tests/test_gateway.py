"""Integration tests: tool call, approval flow, audit."""

import pytest
from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_tool_call_read_file_success():
    r = client.post(
        "/api/tools/call",
        json={
            "agent_id": "agent_001",
            "agent_version": "1.0.0",
            "request_id": "req_001",
            "tool": "read_file",
            "arguments": {"path": "/workspace/readme.md"},
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is True
    assert "result" in data
    assert "audit_id" in data
    assert data["result"].get("path") == "/workspace/readme.md"


def test_tool_call_deny_not_in_registry():
    r = client.post(
        "/api/tools/call",
        json={
            "agent_id": "agent_001",
            "agent_version": "1.0.0",
            "request_id": "req_002",
            "tool": "unknown_tool",
            "arguments": {},
        },
    )
    assert r.status_code == 403
    assert "not in registry" in r.json().get("detail", "").lower() or "deny" in r.json().get("detail", "").lower()


def test_tool_call_deny_role():
    r = client.post(
        "/api/tools/call",
        json={
            "agent_id": "read_only_agent_1",
            "agent_version": "1.0.0",
            "request_id": "req_003",
            "role": "read_only_agent",
            "tool": "delete_file",
            "arguments": {"path": "/tmp/foo"},
        },
    )
    assert r.status_code == 403
    assert "not allowed" in r.json().get("detail", "").lower()


def test_tool_call_pending_approval():
    r = client.post(
        "/api/tools/call",
        json={
            "agent_id": "agent_001",
            "agent_version": "1.0.0",
            "request_id": "req_004",
            "role": "action_agent",
            "tool": "delete_file",
            "arguments": {"path": "/tmp/old.txt"},
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is False
    assert data.get("status") == "pending_approval"
    approval_id = data.get("approval_id")
    assert approval_id

    # Approve and execute
    r2 = client.post("/approve", json={"approval_id": approval_id, "approved": True})
    assert r2.status_code == 200
    data2 = r2.json()
    assert data2["success"] is True
    assert data2["result"].get("deleted") == "/tmp/old.txt"


def test_tool_call_validation_error():
    r = client.post(
        "/api/tools/call",
        json={
            "agent_id": "agent_001",
            "agent_version": "1.0.0",
            "request_id": "req_005",
            "tool": "read_file",
            "arguments": {},  # missing required "path"
        },
    )
    assert r.status_code == 400
    assert "path" in r.json().get("detail", "").lower() or "required" in r.json().get("detail", "").lower()
