"""Redaction utilities for sensitive data in traces."""
import re
import hashlib
from typing import Any, Dict


def redact_pii(text: str) -> str:
    """Redact PII from text."""
    # Email
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', text)
    # Phone
    text = re.sub(r'\b\d{3}-\d{3}-\d{4}\b', '[PHONE]', text)
    # SSN
    text = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[SSN]', text)
    return text


def redact_attributes(attributes: Dict[str, Any]) -> Dict[str, Any]:
    """Redact sensitive attributes."""
    redacted = {}
    sensitive_keys = ['prompt', 'user_input', 'tool_output', 'api_key', 'password']
    
    for key, value in attributes.items():
        if key in sensitive_keys:
            if isinstance(value, str):
                redacted[key] = redact_pii(value)
            else:
                redacted[key] = '[REDACTED]'
        else:
            redacted[key] = value
    
    return redacted


def safe_prompt_attribute(prompt: str, max_length: int = 100) -> Dict[str, str]:
    """Create safe prompt attributes."""
    prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()[:16]
    prompt_sample = prompt[:max_length] + "..." if len(prompt) > max_length else prompt
    
    return {
        "prompt.hash": prompt_hash,
        "prompt.sample": redact_pii(prompt_sample),
        "prompt.length": len(prompt)
    }

