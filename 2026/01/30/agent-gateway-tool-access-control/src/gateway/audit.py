"""Structured audit logs with redaction of secrets and PII."""

import re
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

# Patterns to redact (replace with placeholder)
REDACTION_PATTERNS = [
    (re.compile(r"api[_-]?key[\"'\s:=]+[\w\-]{20,}", re.I), "REDACTED_API_KEY"),
    (re.compile(r"password[\"'\s:=]+[^\"'\s]+", re.I), "REDACTED_PASSWORD"),
    (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"), "REDACTED_EMAIL"),
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "REDACTED_SSN"),
]


SENSITIVE_KEYS = ("password", "api_key", "token", "secret", "authorization")


def redact_value(value: Any, key: Optional[str] = None) -> Any:
    """Redact sensitive data from a value. Keys matching SENSITIVE_KEYS get value redacted."""
    if isinstance(value, str):
        if key and key.lower() in SENSITIVE_KEYS:
            return "REDACTED"
        out = value
        for pattern, replacement in REDACTION_PATTERNS:
            out = pattern.sub(replacement, out)
        return out
    if isinstance(value, dict):
        return {k: redact_value(v, key=k) for k, v in value.items()}
    if isinstance(value, list):
        return [redact_value(item, key=key) for item in value]
    return value


def audit_id() -> str:
    return f"audit_{uuid.uuid4().hex[:16]}"


def log_audit(
    request_id: str,
    agent_id: str,
    agent_version: str,
    tool: str,
    role: str,
    policy_decision: str,
    outcome: str,
    inputs_redacted: dict,
    error_message: Optional[str] = None,
    duration_ms: Optional[float] = None,
    approval_id: Optional[str] = None,
) -> dict:
    """Build one immutable audit log entry (redacted)."""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "audit_id": audit_id(),
        "request_id": request_id,
        "agent_id": agent_id,
        "agent_version": agent_version,
        "tool": tool,
        "role": role,
        "policy_decision": policy_decision,
        "outcome": outcome,
        "inputs_redacted": redact_value(inputs_redacted),
        "duration_ms": duration_ms,
        "approval_id": approval_id,
    }
    if error_message:
        entry["error"] = error_message
    # In production, append to immutable store (e.g. S3, WAL). Here we just return.
    print(f"[AUDIT] {entry}")
    return entry
