"""Observability: logging and metrics for structured outputs."""
import hashlib
import logging
import time
from datetime import datetime
from typing import Any, Optional
from prometheus_client import Counter, Histogram

# Set up logging
logger = logging.getLogger(__name__)

# Prometheus metrics
parse_errors = Counter(
    'llm_json_parse_errors_total',
    'Total JSON parse errors',
    ['schema_name', 'model_name']
)

validation_errors = Counter(
    'llm_json_validation_errors_total',
    'Total schema validation errors',
    ['schema_name', 'field_name']
)

response_time = Histogram(
    'llm_structured_output_duration_seconds',
    'Time to get structured output',
    ['schema_name', 'model_name']
)

success_count = Counter(
    'llm_structured_output_success_total',
    'Total successful structured outputs',
    ['schema_name', 'model_name']
)


def hash_prompt(prompt: str) -> str:
    """Create a hash of the prompt for tracking."""
    return hashlib.md5(prompt.encode()).hexdigest()[:8]


def log_structured_output_call(
    prompt_hash: str,
    raw_response: str,
    parsed_json: dict | None,
    validation_errors_list: list[dict] | None,
    success: bool,
    duration_ms: int,
    schema_name: str,
    model_name: str,
    attempt: int = 1
):
    """
    Log a structured output call.
    
    Args:
        prompt_hash: Hash of the prompt
        raw_response: Raw response from LLM
        parsed_json: Parsed JSON (if successful)
        validation_errors_list: List of validation errors (if any)
        success: Whether the call was successful
        duration_ms: Duration in milliseconds
        schema_name: Name of the schema
        model_name: Name of the model
        attempt: Attempt number (for retries)
    """
    log_data = {
        "prompt_hash": prompt_hash,
        "raw_response_length": len(raw_response),
        "parsed_json": parsed_json,
        "validation_errors": validation_errors_list,
        "success": success,
        "duration_ms": duration_ms,
        "schema_name": schema_name,
        "model_name": model_name,
        "attempt": attempt,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if success:
        logger.info("structured_output_success", extra=log_data)
        success_count.labels(
            schema_name=schema_name,
            model_name=model_name
        ).inc()
    else:
        # Log raw response on failure for debugging
        log_data["raw_response"] = raw_response[:500]  # Truncate long responses
        logger.warning("structured_output_failure", extra=log_data)


def track_parse_error(schema_name: str, model_name: str):
    """Track a parse error."""
    parse_errors.labels(
        schema_name=schema_name,
        model_name=model_name
    ).inc()


def track_validation_error(schema_name: str, field_name: str):
    """Track a validation error."""
    validation_errors.labels(
        schema_name=schema_name,
        field_name=field_name
    ).inc()


def track_response_time(schema_name: str, model_name: str, duration_seconds: float):
    """Track response time."""
    response_time.labels(
        schema_name=schema_name,
        model_name=model_name
    ).observe(duration_seconds)

