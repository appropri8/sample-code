"""Redaction helper for removing PII and secrets from span attributes."""

import re
from typing import Any


# Deny list of patterns to redact
REDACTION_PATTERNS = [
    (r'api[_-]?key["\s:=]+([a-zA-Z0-9_\-]{20,})', 'REDACTED_API_KEY'),
    (r'password["\s:=]+([^\s"\']+)', 'REDACTED_PASSWORD'),
    (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', 'REDACTED_EMAIL'),
    (r'\b\d{3}-\d{2}-\d{4}\b', 'REDACTED_SSN'),  # SSN pattern
    (r'sk-[a-zA-Z0-9]{32,}', 'REDACTED_SK_KEY'),  # OpenAI API key pattern
    (r'Bearer\s+[a-zA-Z0-9_\-]{20,}', 'REDACTED_BEARER_TOKEN'),
]


def redact_value(value: Any) -> Any:
    """Redact sensitive data from a value.
    
    Args:
        value: Value to redact (string, dict, list, or other)
    
    Returns:
        Redacted value with same structure
    """
    if isinstance(value, str):
        redacted = value
        for pattern, replacement in REDACTION_PATTERNS:
            redacted = re.sub(pattern, replacement, redacted, flags=re.IGNORECASE)
        return redacted
    elif isinstance(value, dict):
        return {k: redact_value(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [redact_value(item) for item in value]
    else:
        return value


def set_attribute_safe(span, key: str, value: Any):
    """Set span attribute with redaction.
    
    Args:
        span: OpenTelemetry span
        key: Attribute key
        value: Attribute value (will be redacted)
    """
    redacted = redact_value(value)
    
    # Convert to string if needed (OTel attributes need to be primitive types)
    if isinstance(redacted, (dict, list)):
        import json
        redacted = json.dumps(redacted)
    
    span.set_attribute(key, redacted)
