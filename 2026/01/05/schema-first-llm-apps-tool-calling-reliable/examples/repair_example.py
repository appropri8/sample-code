"""Example: Repair loop with automatic retry."""

from src.schemas import CustomerExtraction
from src.repair_loop import repair_loop, safe_extract


def mock_llm_call_that_fails_then_succeeds(prompt):
    """Mock LLM that fails first time, succeeds second time."""
    global call_count
    if 'call_count' not in globals():
        call_count = 0
    
    call_count += 1
    
    if call_count == 1:
        # First call: missing email
        print(f"  Attempt {call_count}: Missing email field")
        return '{"name": "John Doe", "priority": 3}'
    else:
        # Second call: fixed
        print(f"  Attempt {call_count}: Fixed - includes email")
        return '{"name": "John Doe", "email": "john@example.com", "priority": 3, "tags": []}'


def mock_llm_call_that_always_fails(prompt):
    """Mock LLM that always returns invalid output."""
    return '{"name": "John Doe", "priority": 3}'  # Missing email


def main():
    """Demonstrate repair loop functionality."""
    
    print("Example 1: Repair loop succeeds on retry")
    print("=" * 50)
    global call_count
    call_count = 0
    
    result = repair_loop(
        "Extract customer info: John Doe, john@example.com, priority 3",
        CustomerExtraction,
        llm_call=mock_llm_call_that_fails_then_succeeds,
        max_retries=2
    )
    
    if result:
        print(f"✅ Success: {result.name}, {result.email}, priority {result.priority}")
    else:
        print("❌ Failed after retries")
    print()
    
    print("Example 2: Repair loop fails after max retries")
    print("=" * 50)
    call_count = 0
    
    result = repair_loop(
        "Extract customer info: John Doe, priority 3",
        CustomerExtraction,
        llm_call=mock_llm_call_that_always_fails,
        max_retries=2
    )
    
    if result:
        print(f"✅ Success: {result.name}")
    else:
        print("❌ Failed after max retries (expected)")
    print()
    
    print("Example 3: Safe extract with fallback")
    print("=" * 50)
    call_count = 0
    
    fallback = CustomerExtraction(
        name="Fallback User",
        email="fallback@example.com",
        priority=1
    )
    
    result = safe_extract(
        "Extract customer info",
        CustomerExtraction,
        llm_call=mock_llm_call_that_always_fails,
        fallback=fallback
    )
    
    print(f"✅ Result (with fallback): {result.name}, {result.email}")
    print()


if __name__ == "__main__":
    main()
