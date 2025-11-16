"""Retry and timeout utilities for tool calls."""

import asyncio
import random
import logging
from typing import Callable, TypeVar, Any, Optional
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar('T')


def should_retry(error: Exception) -> bool:
    """Decide if an error should be retried."""
    # Don't retry client errors (4xx)
    if hasattr(error, 'status_code'):
        if 400 <= error.status_code < 500:
            return False
    
    # Don't retry validation errors
    if isinstance(error, (ValueError, KeyError, TypeError, PermissionError)):
        return False
    
    # Retry server errors (5xx) and timeouts
    return True


async def retry_with_backoff(
    func: Callable[[], T],
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    timeout: Optional[float] = None
) -> T:
    """
    Retry a function with exponential backoff and optional timeout.
    
    Args:
        func: Async function to retry
        max_attempts: Maximum number of attempts
        base_delay: Base delay in seconds for exponential backoff
        max_delay: Maximum delay in seconds
        timeout: Optional timeout per attempt
    
    Returns:
        Result from function
    
    Raises:
        Last exception if all retries fail
    """
    last_error = None
    
    for attempt in range(max_attempts):
        try:
            # Apply timeout if specified
            if timeout:
                result = await asyncio.wait_for(func(), timeout=timeout)
            else:
                result = await func()
            
            # Success - log if retried
            if attempt > 0:
                logger.info(f"Function succeeded after {attempt + 1} attempts")
            
            return result
        
        except asyncio.TimeoutError as e:
            last_error = e
            logger.warning(f"Timeout on attempt {attempt + 1}/{max_attempts}")
            
            # Don't retry if it's the last attempt
            if attempt == max_attempts - 1:
                break
        
        except Exception as e:
            last_error = e
            
            # Don't retry on certain errors
            if not should_retry(e):
                logger.warning(f"Error not retryable: {e}")
                raise
            
            logger.warning(f"Error on attempt {attempt + 1}/{max_attempts}: {e}")
            
            # Last attempt - don't wait
            if attempt == max_attempts - 1:
                break
            
            # Calculate delay with jitter
            delay = min(base_delay * (2 ** attempt), max_delay)
            jitter = random.uniform(0, delay * 0.1)
            await asyncio.sleep(delay + jitter)
    
    # All retries exhausted
    logger.error(f"All {max_attempts} attempts failed. Last error: {last_error}")
    raise last_error


def with_timeout_and_retry(
    timeout: float,
    max_retries: int = 3,
    base_delay: float = 1.0
):
    """
    Decorator to add timeout and retry to an async function.
    
    Args:
        timeout: Timeout in seconds per attempt
        max_retries: Maximum number of retries
        base_delay: Base delay for exponential backoff
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            async def call_func():
                return await func(*args, **kwargs)
            
            return await retry_with_backoff(
                call_func,
                max_attempts=max_retries,
                base_delay=base_delay,
                timeout=timeout
            )
        
        return wrapper
    return decorator


# Example usage
if __name__ == "__main__":
    import time
    
    async def unreliable_function():
        """Example function that sometimes fails."""
        await asyncio.sleep(0.1)
        if random.random() < 0.7:  # 70% failure rate
            raise Exception("Random failure")
        return "Success"
    
    async def main():
        try:
            result = await retry_with_backoff(
                unreliable_function,
                max_attempts=5,
                base_delay=0.5,
                timeout=2.0
            )
            print(f"Result: {result}")
        except Exception as e:
            print(f"Failed after retries: {e}")
    
    asyncio.run(main())

