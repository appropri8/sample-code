"""Schema validation examples."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.schema import TaskTriage, Category
from src.validator import validate_json, format_validation_error
from pydantic import ValidationError


def main():
    """Demonstrate schema validation."""
    print("Schema Validation Examples\n" + "=" * 50)
    
    test_cases = [
        # Valid data
        {
            "name": "Valid data",
            "data": {"category": "bug", "priority": 3, "needs_human": True},
            "should_pass": True
        },
        
        # Missing required field
        {
            "name": "Missing required field",
            "data": {"category": "bug", "priority": 3},
            "should_pass": False
        },
        
        # Invalid enum value
        {
            "name": "Invalid enum value",
            "data": {"category": "invalid", "priority": 3, "needs_human": True},
            "should_pass": False
        },
        
        # Invalid priority (out of range)
        {
            "name": "Priority out of range",
            "data": {"category": "bug", "priority": 10, "needs_human": True},
            "should_pass": False
        },
        
        # Extra field (should be rejected)
        {
            "name": "Extra field",
            "data": {"category": "bug", "priority": 3, "needs_human": True, "extra": "field"},
            "should_pass": False
        },
    ]
    
    for test_case in test_cases:
        print(f"\n{test_case['name']}:")
        print(f"Data: {test_case['data']}")
        
        try:
            result = validate_json(test_case['data'], TaskTriage)
            if test_case['should_pass']:
                print(f"✓ Validation passed: {result}")
            else:
                print(f"✗ Validation should have failed but passed!")
        except ValueError as e:
            if test_case['should_pass']:
                print(f"✗ Validation should have passed but failed: {e}")
            else:
                print(f"✓ Validation correctly failed: {str(e)[:100]}...")


if __name__ == "__main__":
    main()

