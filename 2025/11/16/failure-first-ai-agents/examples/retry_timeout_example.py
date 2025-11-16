"""Example of retry and timeout patterns."""

import asyncio
import random
import logging
from src.retry_timeout import retry_with_backoff, with_timeout_and_retry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def unreliable_api_call():
    """Simulate an unreliable API call."""
    await asyncio.sleep(0.1)
    
    # 70% failure rate
    if random.random() < 0.7:
        raise Exception("API call failed")
    
    return "API call succeeded"


async def slow_api_call():
    """Simulate a slow API call."""
    delay = random.uniform(0.5, 2.0)
    await asyncio.sleep(delay)
    return f"API call completed after {delay:.2f}s"


@with_timeout_and_retry(timeout=1.0, max_retries=3, base_delay=0.5)
async def decorated_api_call():
    """API call with timeout and retry decorator."""
    await asyncio.sleep(0.1)
    if random.random() < 0.6:
        raise Exception("Decorated call failed")
    return "Decorated call succeeded"


async def main():
    """Run retry and timeout examples."""
    print("=== Example 1: Retry with Backoff ===\n")
    
    try:
        result = await retry_with_backoff(
            unreliable_api_call,
            max_attempts=5,
            base_delay=0.5,
            timeout=2.0
        )
        print(f"Success: {result}\n")
    except Exception as e:
        print(f"Failed after retries: {e}\n")
    
    print("=== Example 2: Timeout Handling ===\n")
    
    try:
        result = await retry_with_backoff(
            slow_api_call,
            max_attempts=2,
            base_delay=0.5,
            timeout=0.8  # Timeout shorter than some calls
        )
        print(f"Success: {result}\n")
    except asyncio.TimeoutError as e:
        print(f"Timeout occurred: {e}\n")
    except Exception as e:
        print(f"Error: {e}\n")
    
    print("=== Example 3: Decorator Pattern ===\n")
    
    try:
        result = await decorated_api_call()
        print(f"Success: {result}\n")
    except Exception as e:
        print(f"Failed: {e}\n")


if __name__ == "__main__":
    asyncio.run(main())

