"""Repair loop for LLM outputs with validation and retry logic."""

import json
import logging
from typing import Type, Optional
from pydantic import BaseModel

from .validator import extract_json, validate_output

logger = logging.getLogger(__name__)


def build_repair_prompt(
    original_prompt: str,
    validation_errors: str,
    schema: Type[BaseModel]
) -> str:
    """Build prompt asking model to fix validation errors.
    
    Args:
        original_prompt: Original prompt sent to model
        validation_errors: Formatted validation error messages
        schema: Pydantic model class
        
    Returns:
        Repair prompt string
    """
    schema_json = schema.model_json_schema()
    
    return f"""Your previous response had validation errors:
{validation_errors}

Please correct ONLY the fields mentioned in the errors above. Keep all other fields exactly as they were.

Return valid JSON matching this schema:
{json.dumps(schema_json, indent=2)}

Original request:
{original_prompt}"""


def mock_llm_call(prompt: str) -> str:
    """Mock LLM call for testing.
    
    In production, replace with actual LLM API call.
    """
    # This is a mock - in real code, call OpenAI, Anthropic, etc.
    logger.debug(f"Mock LLM call with prompt: {prompt[:100]}...")
    
    # For testing, return a simple response
    # In production, this would be: return openai_client.chat.completions.create(...)
    return '{"name": "John Doe", "email": "john@example.com", "priority": 3, "tags": []}'


def repair_loop(
    prompt: str,
    schema: Type[BaseModel],
    llm_call=None,
    max_retries: int = 2
) -> Optional[BaseModel]:
    """Call model, validate, repair if needed.
    
    Args:
        prompt: Initial prompt for LLM
        schema: Pydantic model class to validate against
        llm_call: Optional function to call LLM (defaults to mock)
        max_retries: Maximum number of repair attempts (default 2)
        
    Returns:
        Validated model instance, or None if all retries fail
    """
    if llm_call is None:
        llm_call = mock_llm_call
    
    current_prompt = prompt
    schema_json = schema.model_json_schema()
    
    for attempt in range(max_retries + 1):
        logger.info(f"Attempt {attempt + 1}/{max_retries + 1}")
        
        # Call model
        response = llm_call(current_prompt)
        data = extract_json(response)
        
        if data is None:
            logger.warning(f"Failed to extract JSON on attempt {attempt + 1}")
            if attempt < max_retries:
                current_prompt = f"{prompt}\n\nPlease return valid JSON only. No extra text."
                continue
            return None
        
        # Validate
        model, error = validate_output(data, schema)
        if model is not None:
            logger.info(f"Validation succeeded on attempt {attempt + 1}")
            return model
        
        # Repair
        logger.warning(f"Validation failed on attempt {attempt + 1}: {error}")
        if attempt < max_retries:
            current_prompt = build_repair_prompt(prompt, error, schema)
        else:
            logger.error(f"All repair attempts failed. Last error: {error}")
            return None
    
    return None


def safe_extract(
    prompt: str,
    schema: Type[BaseModel],
    llm_call=None,
    fallback: Optional[BaseModel] = None
) -> BaseModel:
    """Extract with repair loop, fallback on failure.
    
    Args:
        prompt: Initial prompt for LLM
        schema: Pydantic model class to validate against
        llm_call: Optional function to call LLM
        fallback: Optional fallback model instance
        
    Returns:
        Validated model instance
        
    Raises:
        ValueError: If extraction fails and no fallback provided
    """
    result = repair_loop(prompt, schema, llm_call=llm_call, max_retries=2)
    
    if result is None:
        logger.error(f"Failed to extract after retries: {prompt[:100]}")
        if fallback is not None:
            logger.warning("Using fallback after repair failure")
            return fallback
        raise ValueError("Failed to extract after retries and no fallback provided")
    
    return result
