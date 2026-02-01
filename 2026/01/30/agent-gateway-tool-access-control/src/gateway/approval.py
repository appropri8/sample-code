"""Approval flow: pending queue, approve, then execute."""

import uuid
from typing import Any, Dict

# approval_id -> pending request payload
_pending: Dict[str, dict] = {}


def create_pending(envelope: dict, tool: str, arguments: dict) -> str:
    """Store request as pending; return approval_id."""
    approval_id = f"approv_{uuid.uuid4().hex[:12]}"
    _pending[approval_id] = {
        "envelope": envelope,
        "tool": tool,
        "arguments": arguments,
    }
    return approval_id


def get_pending(approval_id: str):
    """Return pending request if exists."""
    return _pending.get(approval_id)


def consume_pending(approval_id: str):
    """Remove and return pending request (one-time use)."""
    return _pending.pop(approval_id, None)
