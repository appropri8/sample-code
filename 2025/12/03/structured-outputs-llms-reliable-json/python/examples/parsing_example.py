"""JSON parsing examples."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.parser import extract_json, extract_json_simple


def main():
    """Demonstrate JSON parsing from various formats."""
    print("JSON Parsing Examples\n" + "=" * 50)
    
    test_cases = [
        # Valid JSON
        ('{"category": "bug", "priority": 3}'),
        
        # JSON with markdown
        ('```json\n{"category": "bug", "priority": 3}\n```'),
        
        # JSON with explanation
        ('Here\'s the JSON: {"category": "bug", "priority": 3}'),
        
        # JSON with both
        ('Here\'s the result:\n```json\n{"category": "bug", "priority": 3}\n```\nThis is a bug report.'),
        
        # JSON array
        ('[{"category": "bug"}, {"category": "feature"}]'),
        
        # Nested JSON
        ('{"task": {"category": "bug", "priority": 3}}'),
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}:")
        print(f"Input: {test_case[:60]}...")
        try:
            result = extract_json(test_case)
            print(f"Success: {result}")
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()

