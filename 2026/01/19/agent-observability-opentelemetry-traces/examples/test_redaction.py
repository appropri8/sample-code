"""Example: Test redaction helper."""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.redaction import redact_value, set_attribute_safe
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, BatchSpanProcessor

# Setup tracer
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

exporter = ConsoleSpanExporter()
processor = BatchSpanProcessor(exporter)
trace.get_tracer_provider().add_span_processor(processor)


def test_redaction():
    """Test redaction patterns."""
    
    test_cases = [
        ("api_key=sk-1234567890abcdef", "REDACTED_SK_KEY"),
        ("password=secret123", "REDACTED_PASSWORD"),
        ("email: user@example.com", "REDACTED_EMAIL"),
        ("SSN: 123-45-6789", "REDACTED_SSN"),
        ("Bearer token1234567890", "REDACTED_BEARER_TOKEN"),
    ]
    
    print("Testing redaction patterns:")
    print("-" * 60)
    
    for original, expected_pattern in test_cases:
        redacted = redact_value(original)
        print(f"Original: {original}")
        print(f"Redacted: {redacted}")
        print(f"Contains expected pattern: {expected_pattern in redacted}")
        print()
    
    # Test with span attributes
    print("\nTesting span attribute redaction:")
    print("-" * 60)
    
    with tracer.start_as_current_span("test.span") as span:
        # These should be redacted
        set_attribute_safe(span, "user.email", "test@example.com")
        set_attribute_safe(span, "api.key", "sk-1234567890abcdef")
        set_attribute_safe(span, "credentials.password", "secret123")
        
        # This should not be redacted
        set_attribute_safe(span, "tool.name", "read_file")
        set_attribute_safe(span, "tool.status", "success")
        
        print("Span attributes set (check console output for redacted values)")
    
    trace.get_tracer_provider().force_flush()


if __name__ == "__main__":
    test_redaction()
