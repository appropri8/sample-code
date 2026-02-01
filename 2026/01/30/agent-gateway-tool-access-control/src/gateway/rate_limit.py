"""Simple in-memory rate limiting and timeout tracking per agent."""

import time
from collections import defaultdict
from typing import Optional

# agent_id -> list of (timestamp, request_id)
_calls: defaultdict[str, list[tuple[float, str]]] = defaultdict(list)

# Config
RATE_LIMIT_WINDOW_SEC = 60
RATE_LIMIT_MAX_CALLS = 100
DEFAULT_TIMEOUT_SEC = 30


def check_rate_limit(agent_id: str, request_id: str) -> tuple:
    """
    Returns (allowed, error_message).
    Enforces max RATE_LIMIT_MAX_CALLS per agent per RATE_LIMIT_WINDOW_SEC.
    """
    now = time.time()
    cutoff = now - RATE_LIMIT_WINDOW_SEC
    # Drop old entries
    _calls[agent_id] = [(ts, rid) for ts, rid in _calls[agent_id] if ts > cutoff]
    if len(_calls[agent_id]) >= RATE_LIMIT_MAX_CALLS:
        return False, f"Rate limit exceeded: max {RATE_LIMIT_MAX_CALLS} calls per {RATE_LIMIT_WINDOW_SEC}s"
    _calls[agent_id].append((now, request_id))
    return True, None


def record_call(agent_id: str, request_id: str) -> None:
    """Record a call for rate limit accounting (called after policy allow)."""
    # Already recorded in check_rate_limit
    pass
