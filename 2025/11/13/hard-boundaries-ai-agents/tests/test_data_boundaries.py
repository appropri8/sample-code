"""Tests for data boundaries"""

from src.data_boundaries import redact_pii, prepare_safe_input, AgentRequest


def test_pii_redaction():
    """Test PII redaction"""
    text = "Contact me at john@example.com or call 555-123-4567"
    redacted = redact_pii(text)
    
    assert "[EMAIL]" in redacted
    assert "[PHONE]" in redacted
    assert "john@example.com" not in redacted
    assert "555-123-4567" not in redacted


def test_safe_input():
    """Test safe input preparation"""
    user_input = "I need help with my account"
    context = {
        "email": "john@example.com",
        "phone": "555-123-4567"
    }
    
    safe_input = prepare_safe_input(user_input, context)
    
    assert "[EMAIL]" in safe_input
    assert "[PHONE]" in safe_input
    assert "john@example.com" not in safe_input


def test_agent_request():
    """Test AgentRequest"""
    request = AgentRequest(
        user_id="user_123",
        task_context={"key": "value"}
    )
    
    assert request.get_identity() == "user_123"
    prompt = request.to_prompt()
    assert "user_123" not in prompt
    assert "value" in prompt

