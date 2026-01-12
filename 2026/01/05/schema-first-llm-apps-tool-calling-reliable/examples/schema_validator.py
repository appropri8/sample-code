"""Example: Schema + Validator with clear error reporting."""

from src.schemas import CustomerExtraction
from src.validator import extract_json, validate_output


def main():
    """Demonstrate schema validation with error reporting."""
    
    # Example 1: Valid JSON
    print("Example 1: Valid JSON")
    response1 = '{"name": "John Doe", "email": "john@example.com", "priority": 3, "tags": ["vip"]}'
    data1 = extract_json(response1)
    model1, error1 = validate_output(data1, CustomerExtraction)
    
    if model1:
        print(f"✅ Valid: {model1.name}, {model1.email}, priority {model1.priority}")
    else:
        print(f"❌ Error: {error1}")
    print()
    
    # Example 2: Missing required field
    print("Example 2: Missing required field")
    response2 = '{"name": "John Doe", "priority": 3}'
    data2 = extract_json(response2)
    model2, error2 = validate_output(data2, CustomerExtraction)
    
    if model2:
        print(f"✅ Valid: {model2.name}")
    else:
        print(f"❌ Error: {error2}")
        print(f"   Path: $.customer.email (missing)")
    print()
    
    # Example 3: Wrong type
    print("Example 3: Wrong type")
    response3 = '{"name": "John Doe", "email": "john@example.com", "priority": "high"}'
    data3 = extract_json(response3)
    model3, error3 = validate_output(data3, CustomerExtraction)
    
    if model3:
        print(f"✅ Valid: {model3.name}")
    else:
        print(f"❌ Error: {error3}")
        print(f"   Path: $.customer.priority (expected integer 1-5, got string)")
    print()
    
    # Example 4: Trailing comma (should be fixed by extract_json)
    print("Example 4: Trailing comma")
    response4 = '{"name": "John Doe", "email": "john@example.com", "priority": 3,}'
    data4 = extract_json(response4)
    model4, error4 = validate_output(data4, CustomerExtraction)
    
    if model4:
        print(f"✅ Valid (trailing comma fixed): {model4.name}")
    else:
        print(f"❌ Error: {error4}")
    print()
    
    # Example 5: Invalid email format
    print("Example 5: Invalid email format")
    response5 = '{"name": "John Doe", "email": "not-an-email", "priority": 3}'
    data5 = extract_json(response5)
    model5, error5 = validate_output(data5, CustomerExtraction)
    
    if model5:
        print(f"✅ Valid: {model5.name}")
    else:
        print(f"❌ Error: {error5}")
        print(f"   Path: $.customer.email (invalid format)")


if __name__ == "__main__":
    main()
