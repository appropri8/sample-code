"""JSON extraction and validation with clear error reporting."""

import json
import re
from typing import Type, Optional
from pydantic import BaseModel, ValidationError


def extract_json(text: str) -> Optional[dict]:
    """Extract JSON from text, handling common issues.
    
    Handles:
    - Markdown code blocks (```json ... ```)
    - Extra text before/after JSON
    - Trailing commas
    - Multiple JSON objects (returns first)
    
    Args:
        text: Text that may contain JSON
        
    Returns:
        Parsed JSON dict, or None if extraction fails
    """
    # Remove markdown code blocks
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*$', '', text)
    text = text.strip()
    
    # Find JSON object
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if not match:
        return None
    
    json_str = match.group(0)
    
    # Try to parse
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        # Try fixing trailing commas
        json_str = re.sub(r',\s*}', '}', json_str)
        json_str = re.sub(r',\s*]', ']', json_str)
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            return None


def validate_output(
    data: dict,
    schema: Type[BaseModel]
) -> tuple[Optional[BaseModel], Optional[str]]:
    """Validate data against schema, return model or error.
    
    Args:
        data: Parsed JSON data
        schema: Pydantic model class to validate against
        
    Returns:
        Tuple of (validated_model, error_message)
        - If valid: (model, None)
        - If invalid: (None, formatted_error_string)
    """
    try:
        model = schema(**data)
        return model, None
    except ValidationError as e:
        # Format errors for repair
        errors = []
        for error in e.errors():
            # Build path string like "customer.address.zip"
            path_parts = [str(x) for x in error["loc"]]
            path = " -> ".join(path_parts) if path_parts else "root"
            
            # Get error message
            msg = error["msg"]
            error_type = error["type"]
            
            # Format: "path: message (type)"
            errors.append(f"{path}: {msg} (type: {error_type})")
        
        error_message = "; ".join(errors)
        return None, error_message
