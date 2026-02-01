"""Tests for audit log redaction of secrets and PII."""

from src.gateway.audit import redact_value, REDACTION_PATTERNS


def test_redact_email():
    out = redact_value("Contact me at user@example.com for details")
    assert "user@example.com" not in out
    assert "REDACTED_EMAIL" in out


def test_redact_api_key():
    out = redact_value({"api_key": "sk-1234567890abcdef"})
    assert out.get("api_key") != "sk-1234567890abcdef"
    assert "REDACTED" in str(out.get("api_key", ""))


def test_redact_nested():
    out = redact_value({"args": {"path": "/tmp", "password": "secret123"}})
    assert out["args"]["path"] == "/tmp"
    assert out["args"]["password"] == "REDACTED"


def test_redact_preserves_non_sensitive():
    out = redact_value({"tool": "read_file", "path": "/workspace/doc.txt"})
    assert out["tool"] == "read_file"
    assert out["path"] == "/workspace/doc.txt"
