"""Auto-repair common JSON issues."""
import json
import re
from typing import Any


def repair_json(text: str) -> dict | list | None:
    """
    Attempt to repair common JSON issues without retrying the LLM.
    
    Handles:
    - Single quotes to double quotes (simple cases)
    - Trailing commas
    - Comments (simple cases)
    - Extra whitespace
    
    Args:
        text: Potentially broken JSON string
    
    Returns:
        Repaired JSON object/array or None if repair fails
    """
    if not text or not text.strip():
        return None
    
    # Remove comments (simple cases)
    # Remove // comments
    text = re.sub(r'//.*?$', '', text, flags=re.MULTILINE)
    # Remove /* */ comments
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
    
    # Remove trailing commas before } or ]
    text = re.sub(r',(\s*[}\]])', r'\1', text)
    
    # Try to fix single quotes to double quotes (very simple cases only)
    # This is risky, so we only do it for obvious cases
    # Match: 'key': 'value' or 'key': "value"
    text = re.sub(r"'([^']*)':\s*", r'"\1": ', text)
    # Match: "key": 'value'
    text = re.sub(r":\s*'([^']*)'", r': "\1"', text)
    
    # Trim whitespace
    text = text.strip()
    
    # Try parsing
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def fix_trailing_comma(text: str) -> str:
    """Remove trailing commas from JSON."""
    return re.sub(r',(\s*[}\]])', r'\1', text)


def remove_comments(text: str) -> str:
    """Remove comments from JSON-like text."""
    # Remove // comments
    text = re.sub(r'//.*?$', '', text, flags=re.MULTILINE)
    # Remove /* */ comments
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
    return text

