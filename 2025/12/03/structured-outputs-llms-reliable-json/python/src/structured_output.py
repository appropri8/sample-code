"""Complete structured output pipeline."""
import time
from typing import Type, TypeVar
from pydantic import BaseModel, ValidationError

from .llm_client import StructuredLLM
from .parser import extract_json
from .validator import validate_json, format_validation_error
from .repair import repair_json
from .prompt_builder import build_structured_prompt, add_error_feedback
from .observability import (
    log_structured_output_call,
    track_parse_error,
    track_validation_error,
    track_response_time,
    hash_prompt
)

T = TypeVar('T', bound=BaseModel)


def get_structured_output(
    llm: StructuredLLM,
    prompt: str,
    schema: Type[T],
    max_retries: int = 3,
    enable_repair: bool = True,
    use_json_mode: bool = False
) -> T:
    """
    Get structured output from LLM with parsing, validation, and retry logic.
    
    Args:
        llm: LLM client instance
        prompt: Input prompt
        schema: Pydantic model class
        max_retries: Maximum number of retry attempts
        enable_repair: Whether to attempt JSON repair before retrying
        use_json_mode: Whether to use JSON mode (if supported by model)
    
    Returns:
        Validated model instance
    
    Raises:
        ValueError: If unable to get valid structured output after retries
    """
    prompt_hash = hash_prompt(prompt)
    schema_name = schema.__name__
    model_name = llm.model_name
    original_prompt = prompt
    last_error = None
    
    for attempt in range(max_retries):
        start_time = time.time()
        
        try:
            # Call LLM
            raw_response = llm.generate(prompt, use_json_mode=use_json_mode)
            
            # Try repair first (if enabled)
            json_data = None
            if enable_repair:
                json_data = repair_json(raw_response)
            
            # Extract JSON if repair didn't work
            if json_data is None:
                try:
                    json_data = extract_json(raw_response)
                except ValueError as e:
                    last_error = f"JSON parsing failed: {str(e)}"
                    duration_ms = int((time.time() - start_time) * 1000)
                    
                    track_parse_error(schema_name, model_name)
                    log_structured_output_call(
                        prompt_hash=prompt_hash,
                        raw_response=raw_response,
                        parsed_json=None,
                        validation_errors_list=None,
                        success=False,
                        duration_ms=duration_ms,
                        schema_name=schema_name,
                        model_name=model_name,
                        attempt=attempt + 1
                    )
                    
                    if attempt < max_retries - 1:
                        prompt = add_error_feedback(original_prompt, last_error, raw_response)
                        continue
                    raise ValueError(f"Failed to parse JSON after {max_retries} attempts: {last_error}")
            
            # Validate
            try:
                result = validate_json(json_data, schema)
                duration_ms = int((time.time() - start_time) * 1000)
                
                track_response_time(schema_name, model_name, duration_ms / 1000.0)
                log_structured_output_call(
                    prompt_hash=prompt_hash,
                    raw_response=raw_response,
                    parsed_json=json_data,
                    validation_errors_list=None,
                    success=True,
                    duration_ms=duration_ms,
                    schema_name=schema_name,
                    model_name=model_name,
                    attempt=attempt + 1
                )
                
                return result
                
            except ValueError as e:
                last_error = f"Schema validation failed: {str(e)}"
                duration_ms = int((time.time() - start_time) * 1000)
                
                # Extract field name from error if possible
                field_name = "unknown"
                if isinstance(e.__cause__, ValidationError):
                    errors = e.__cause__.errors()
                    if errors:
                        field_name = ".".join(str(loc) for loc in errors[0]["loc"])
                
                track_validation_error(schema_name, field_name)
                log_structured_output_call(
                    prompt_hash=prompt_hash,
                    raw_response=raw_response,
                    parsed_json=json_data,
                    validation_errors_list=[{"error": str(e)}],
                    success=False,
                    duration_ms=duration_ms,
                    schema_name=schema_name,
                    model_name=model_name,
                    attempt=attempt + 1
                )
                
                if attempt < max_retries - 1:
                    prompt = add_error_feedback(original_prompt, last_error, raw_response)
                    continue
                raise ValueError(f"Failed to validate JSON after {max_retries} attempts: {last_error}")
                
        except ValueError as e:
            # Re-raise if it's our error
            if "Failed to" in str(e):
                raise
            # Otherwise, it's an LLM call error
            last_error = f"LLM call failed: {str(e)}"
            duration_ms = int((time.time() - start_time) * 1000)
            
            log_structured_output_call(
                prompt_hash=prompt_hash,
                raw_response="",
                parsed_json=None,
                validation_errors_list=None,
                success=False,
                duration_ms=duration_ms,
                schema_name=schema_name,
                model_name=model_name,
                attempt=attempt + 1
            )
            
            if attempt < max_retries - 1:
                # Don't retry on timeout/API errors immediately
                time.sleep(1)
                continue
            raise ValueError(f"LLM call failed after {max_retries} attempts: {last_error}")
    
    raise ValueError(f"Failed after {max_retries} attempts. Last error: {last_error}")

