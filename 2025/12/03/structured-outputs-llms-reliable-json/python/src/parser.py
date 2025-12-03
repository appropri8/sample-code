"""Extract JSON from raw LLM responses."""
import json
import re
from typing import Any


def extract_json(text: str) -> dict | list:
    """
    Extract JSON from text that might contain markdown, explanations, or extra text.
    
    Args:
        text: Raw text that might contain JSON
    
    Returns:
        Parsed JSON object or array
    
    Raises:
        ValueError: If no valid JSON can be extracted
    """
    # Step 1: Trim whitespace
    text = text.strip()
    
    # Step 2: Remove markdown code blocks
    # Matches ```json ... ``` or ``` ... ```
    text = re.sub(r'```(?:json)?\s*\n?(.*?)\n?```', r'\1', text, flags=re.DOTALL)
    text = text.strip()
    
    # Step 3: Find JSON object/array
    # Look for first { or [
    start = text.find('{')
    if start == -1:
        start = text.find('[')
    if start == -1:
        raise ValueError("No JSON found in response")
    
    # Step 4: Find matching closing brace/bracket
    depth = 0
    in_string = False
    escape_next = False
    
    for i in range(start, len(text)):
        char = text[i]
        
        if escape_next:
            escape_next = False
            continue
        
        if char == '\\':
            escape_next = True
            continue
        
        if char == '"' and not escape_next:
            in_string = not in_string
            continue
        
        if in_string:
            continue
        
        if char == '{' or char == '[':
            depth += 1
        elif char == '}' or char == ']':
            depth -= 1
            if depth == 0:
                json_str = text[start:i+1]
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError as e:
                    raise ValueError(f"Invalid JSON: {str(e)}")
    
    raise ValueError("Unclosed JSON structure")


def extract_json_simple(text: str) -> dict | list | None:
    """
    Simple JSON extraction that tries to parse the entire text.
    Falls back to extract_json if that fails.
    
    Args:
        text: Raw text that might contain JSON
    
    Returns:
        Parsed JSON or None if extraction fails
    """
    text = text.strip()
    
    # Try parsing the whole text first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    # Fall back to full extraction
    try:
        return extract_json(text)
    except ValueError:
        return None

