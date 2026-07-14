"""
Example 4: Retry Logic with Repair Loops

Demonstrates:
- Validation-based retry
- Repair prompts with error feedback
- Exponential backoff
- Max retry limits
"""

import json
import time
from typing import TypeVar
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
        llm_call: callable,
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
    
    @staticmethod
    def retry_with_fallback(
        primary_llm: callable,
        fallback_llm: callable,
        prompt: str,
        schema: type[T],
        config: RetryConfig = RetryConfig()
    ) -> tuple[T | None, str, int]:
        """
        Try primary LLM, fall back to secondary if it fails
        
        Returns:
            Tuple of (validated_result, model_used, retry_count)
        """
        from src.validation_middleware import ValidationMiddleware
        
        # Try primary model
        result, retries, _ = RetryStrategy.retry_with_validation(
            primary_llm,
            prompt,
            schema,
            config
        )
        
        if result is not None:
            return result, "primary", retries
        
        # Fall back to secondary model
        result, retries, _ = RetryStrategy.retry_with_validation(
            fallback_llm,
            prompt,
            schema,
            RetryConfig(max_retries=1)  # Only try once with fallback
        )
        
        return result, "fallback" if result else "failed", retries


def mock_llm_with_errors(prompt: str) -> str:
    """Mock LLM that simulates validation errors then fixes them"""
    
    if "validation errors" in prompt.lower():
        # This is a repair attempt - return valid output
        return """{
            "version": "2.0",
            "title": "Fix authentication bug",
            "priority": 4,
            "category": "bug",
            "description": "Users cannot log in"
        }"""
    else:
        # First attempt - return invalid output
        return """{
            "title": "Fix authentication bug",
            "priority": "high",
            "category": "bug"
        }"""


def mock_llm_always_valid(prompt: str) -> str:
    """Mock LLM that always returns valid output"""
    return """{
        "version": "2.0",
        "title": "Implement feature X",
        "priority": 3,
        "category": "feature"
    }"""


def demonstrate_retry():
    """Demonstrate retry logic"""
    
    from src.schema_definitions import TaskExtractionV2
    
    print("=" * 60)
    print("Example 4: Retry Logic")
    print("=" * 60)
    
    # Test case 1: Successful retry after error
    print("\n1. Retry After Validation Error:")
    result, retries, error_log = RetryStrategy.retry_with_validation(
        mock_llm_with_errors,
        "Extract task from: Fix the critical auth bug",
        TaskExtractionV2,
        RetryConfig(max_retries=2)
    )
    print(f"   Success: {result is not None}")
    print(f"   Retries: {retries}")
    print(f"   Error log:")
    for log in error_log:
        print(f"     {log}")
    if result:
        print(f"   Final result: {result.model_dump_json(indent=2)}")
    
    # Test case 2: Immediate success (no retry)
    print("\n2. Immediate Success:")
    result, retries, error_log = RetryStrategy.retry_with_validation(
        mock_llm_always_valid,
        "Extract task from: Build the dashboard",
        TaskExtractionV2,
        RetryConfig(max_retries=2)
    )
    print(f"   Success: {result is not None}")
    print(f"   Retries: {retries}")
    print(f"   Error log: {error_log}")
    
    # Test case 3: Exponential backoff demonstration
    print("\n3. Exponential Backoff Delays:")
    config = RetryConfig(max_retries=4, initial_delay=0.1, backoff_factor=2.0)
    for i in range(5):
        delay = config.get_delay(i)
        print(f"   Attempt {i + 1}: {delay:.2f}s delay")
    
    # Test case 4: Fallback model
    print("\n4. Fallback Model Strategy:")
    result, model_used, retries = RetryStrategy.retry_with_fallback(
        mock_llm_with_errors,  # Primary will fail first attempt
        mock_llm_always_valid,  # Fallback always works
        "Extract task from: Update the docs",
        TaskExtractionV2
    )
    print(f"   Success: {result is not None}")
    print(f"   Model used: {model_used}")
    print(f"   Retries: {retries}")
    
    print("\n" + "=" * 60)
    print("Retry logic demonstration complete!")
    print("=" * 60)


if __name__ == "__main__":
    import sys
    sys.path.insert(0, '.')
    
    demonstrate_retry()
