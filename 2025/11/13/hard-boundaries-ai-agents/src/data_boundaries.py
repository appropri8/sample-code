"""Data boundaries and PII handling"""

import re
import json
from typing import Dict, Any


def redact_pii(text: str) -> str:
    """Remove PII from text"""
    # Email
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', text)
    
    # Phone
    text = re.sub(r'\b\d{3}-\d{3}-\d{4}\b', '[PHONE]', text)
    
    # Credit card (simple pattern)
    text = re.sub(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b', '[CARD]', text)
    
    # SSN
    text = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[SSN]', text)
    
    return text


def prepare_safe_input(user_input: str, context: Dict[str, Any]) -> str:
    """Prepare input with PII removed"""
    # Redact user input
    safe_input = redact_pii(user_input)
    
    # Redact context
    safe_context = {}
    for key, value in context.items():
        if isinstance(value, str):
            safe_context[key] = redact_pii(value)
        else:
            safe_context[key] = value
    
    return f"User: {safe_input}\nContext: {json.dumps(safe_context)}"


def prepare_agent_context(user_id: str, task: str) -> Dict[str, Any]:
    """Prepare minimal context for agent"""
    # Mock implementations - replace with actual data access
    def get_recent_tickets(uid: str, limit: int):
        return [{"id": f"ticket_{i}", "status": "open"} for i in range(limit)]
    
    def get_account_tier(uid: str):
        return "premium"
    
    def get_current_plan(uid: str):
        return "pro"
    
    def get_billing_history(uid: str, limit: int):
        return [{"amount": 99.99, "date": "2025-01-01"} for _ in range(limit)]
    
    # Get only what's needed
    if task == "support":
        return {
            "user_id": user_id,
            "recent_tickets": get_recent_tickets(user_id, limit=5),
            "account_tier": get_account_tier(user_id)
        }
    elif task == "billing":
        return {
            "user_id": user_id,
            "current_plan": get_current_plan(user_id),
            "billing_history": get_billing_history(user_id, limit=3)
        }
    else:
        return {"user_id": user_id}  # Minimal context


class AgentRequest:
    """Request with separated identity and context"""
    def __init__(self, user_id: str, task_context: Dict[str, Any]):
        self.user_id = user_id  # Kept separate
        self.task_context = task_context  # Sent to model
    
    def to_prompt(self) -> str:
        """Convert to prompt without identity"""
        # Don't include user_id in prompt
        return json.dumps(self.task_context)
    
    def get_identity(self) -> str:
        """Get identity separately"""
        return self.user_id

