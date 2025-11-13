"""Example of data boundaries and PII handling"""

from src.data_boundaries import (
    redact_pii,
    prepare_safe_input,
    prepare_agent_context,
    AgentRequest
)


def example_pii_redaction():
    """Example of PII redaction"""
    print("PII redaction example:")
    
    texts = [
        "Contact me at john.doe@example.com or call 555-123-4567",
        "My SSN is 123-45-6789",
        "Credit card: 1234-5678-9012-3456",
        "No PII here, just regular text"
    ]
    
    for text in texts:
        redacted = redact_pii(text)
        print(f"  Original: {text}")
        print(f"  Redacted: {redacted}\n")


def example_safe_input():
    """Example of preparing safe input"""
    print("Safe input preparation:")
    
    user_input = "I need help with my account john.doe@example.com"
    context = {
        "user_id": "user_123",
        "email": "john.doe@example.com",
        "phone": "555-123-4567",
        "account_tier": "premium"
    }
    
    safe_input = prepare_safe_input(user_input, context)
    print(f"  Safe input: {safe_input}\n")


def example_agent_context():
    """Example of preparing agent context"""
    print("Agent context preparation:")
    
    tasks = ["support", "billing", "other"]
    for task in tasks:
        context = prepare_agent_context("user_123", task)
        print(f"  Task: {task}")
        print(f"  Context: {context}\n")


def example_agent_request():
    """Example of AgentRequest with separated identity"""
    print("AgentRequest example:")
    
    task_context = {
        "recent_tickets": [{"id": "ticket_1", "status": "open"}],
        "account_tier": "premium"
    }
    
    request = AgentRequest(user_id="user_123", task_context=task_context)
    
    print(f"  Identity: {request.get_identity()}")
    print(f"  Prompt (no identity): {request.to_prompt()}")


if __name__ == "__main__":
    example_pii_redaction()
    example_safe_input()
    example_agent_context()
    example_agent_request()

