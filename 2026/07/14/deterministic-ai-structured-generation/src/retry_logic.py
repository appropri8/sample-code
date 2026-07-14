"""
Retry Logic with Repair Loops

Handles validation failures with intelligent retry strategies
"""

import json
import time
from typing import TypeVar, Callable
from pydantic import BaseModel

T = TypeVar('T', bound=BaseModel)


class RetryConfig:
    """Configuration for retry behavior"""
    
    def __init__(
        self,
        max_retries: int = 2,
        initial_delay: float = 0.5,
        backoff_factor: float = 2.0,
        max_delay: float = 10.0
    ):
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.backoff_factor = backoff_factor
        self.max_delay = max_delay
    
    def get_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt with exponential backoff"""
        delay = self.initial_delay * (self.backoff_factor ** attempt)
        return min(delay, self.max_delay)


class RetryStrategy:
    """Retry strategies for failed validations"""
    
    @staticmethod
    def build_repair_prompt(
        original_prompt: str,
        validation_errors: list[str],
        schema: type[BaseModel]
    ) -> str:
        """Build a prompt that asks the model to fix specific errors"""
        
        schema_json = schema.model_json_schema()
        errors_formatted = "\n".join(f"  - {error}" for error in validation_errors)
        
        repair_prompt = f"""Your previous output had validation errors:
{errors_formatted}

Please correct ONLY the fields mentioned in the errors above. Keep all other fields exactly as they were.

Return valid JSON matching this schema:
{json.dumps(schema_json, indent=2)}

Original request:
{original_prompt}

Return only valid JSON, no other text."""
        
        return repair_prompt
    
    @staticmethod
    def retry_with_validation(
        llm_call: Callable[[str], str],
        prompt: str,
        schema: type[T],
        config: RetryConfig = RetryConfig()
    ) -> tuple[T | None, int, list[str]]:
        """
        Retry LLM call with validation and repair prompts
        
        Returns:
            Tuple of (validated_result, retry_count, error_log)
        """
        from src.validation_middleware import ValidationMiddleware
        
        current_prompt = prompt
        error_log = []
        
        for attempt in range(config.max_retries + 1):
            # Call LLM
            response = llm_call(current_prompt)
            
            # Validate
            result = ValidationMiddleware.validate(response, schema)
            
            if result.success:
                return result.data, attempt, error_log
            
            # Log error
            error_log.append(f"Attempt {attempt + 1}: {', '.join(result.errors)}")
            
            # If this was the last attempt, give up
            if attempt >= config.max_retries:
                return None, attempt + 1, error_log
            
            # Build repair prompt for next attempt
            current_prompt = RetryStrategy.build_repair_prompt(
                prompt,
                result.errors,
                schema
            )
            
            # Wait with exponential backoff
            delay = config.get_delay(attempt)
            time.sleep(delay)
        
        return None, config.max_retries + 1, error_log
