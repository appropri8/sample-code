"""
Example 3: Validation Middleware

Reusable validation wrapper that:
- Parses JSON from model output
- Validates against schema
- Returns detailed error messages
- Handles common edge cases
"""

import json
import re
from pydantic import BaseModel, ValidationError
from typing import TypeVar, Generic

T = TypeVar('T', bound=BaseModel)


class ValidationResult(Generic[T]):
    """Result of validation operation"""
    
    def __init__(
        self,
        success: bool,
        data: T | None = None,
        errors: list[str] | None = None,
        raw_output: str | None = None
    ):
        self.success = success
        self.data = data
        self.errors = errors or []
        self.raw_output = raw_output
    
    def __repr__(self) -> str:
        if self.success:
            return f"ValidationResult(success=True, data={self.data})"
        return f"ValidationResult(success=False, errors={self.errors})"


class ValidationMiddleware:
    """Middleware for parsing and validating LLM outputs"""
    
    @staticmethod
    def extract_json(text: str) -> dict | None:
        """
        Extract JSON from text, handling common issues:
        - Markdown code blocks
        - Extra text before/after JSON
        - Trailing commas
        - Unescaped characters
        """
        # Remove markdown code blocks
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*', '', text)
        
        # Remove common prefixes
        text = re.sub(r'^(Here\'s|Here is|The|This is).*?[:]\s*', '', text, flags=re.IGNORECASE)
        
        # Extract first JSON object or array
        pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}|\[[^\[\]]*(?:\[[^\[\]]*\][^\[\]]*)*\]'
        match = re.search(pattern, text, re.DOTALL)
        
        if not match:
            return None
        
        json_str = match.group(0)
        
        # Try to parse
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            # Try fixing common issues
            
            # Fix trailing commas
            json_str = re.sub(r',\s*}', '}', json_str)
            json_str = re.sub(r',\s*]', ']', json_str)
            
            # Fix unquoted keys (basic cases)
            json_str = re.sub(r'(\s*)([a-zA-Z_][a-zA-Z0-9_]*)(\s*):', r'\1"\2"\3:', json_str)
            
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                return None
    
    @staticmethod
    def validate_with_details(
        data: dict,
        schema: type[T]
    ) -> tuple[T | None, list[str]]:
        """
        Validate data against schema and return detailed errors
        
        Returns:
            Tuple of (validated_model, error_messages)
        """
        try:
            validated = schema(**data)
            return validated, []
        except ValidationError as e:
            errors = []
            for error in e.errors():
                # Build field path
                field_path = " -> ".join(str(x) for x in error["loc"])
                error_msg = error["msg"]
                error_type = error["type"]
                
                # Format error message
                if error_type == "missing":
                    errors.append(f"{field_path}: Field is required but missing")
                elif error_type in ["string_type", "int_type", "float_type", "bool_type"]:
                    expected_type = error_type.replace("_type", "")
                    errors.append(f"{field_path}: Expected {expected_type}, got {type(data.get(field_path)).__name__}")
                elif "enum" in error_type:
                    errors.append(f"{field_path}: {error_msg}")
                else:
                    errors.append(f"{field_path}: {error_msg}")
            
            return None, errors
    
    @classmethod
    def validate(
        cls,
        llm_output: str,
        schema: type[T]
    ) -> ValidationResult[T]:
        """
        Complete validation pipeline: parse and validate
        
        Args:
            llm_output: Raw output from LLM
            schema: Pydantic model to validate against
            
        Returns:
            ValidationResult with success status, data, and errors
        """
        # Parse JSON
        parsed = cls.extract_json(llm_output)
        
        if parsed is None:
            return ValidationResult(
                success=False,
                errors=["Failed to parse valid JSON from output"],
                raw_output=llm_output
            )
        
        # Validate against schema
        validated, errors = cls.validate_with_details(parsed, schema)
        
        if validated is not None:
            return ValidationResult(
                success=True,
                data=validated,
                raw_output=llm_output
            )
        
        return ValidationResult(
            success=False,
            errors=errors,
            raw_output=llm_output
        )


def demonstrate_validation():
    """Demonstrate validation middleware"""
    
    from src.schema_definitions import TaskExtractionV2
    
    print("=" * 60)
    print("Example 3: Validation Middleware")
    print("=" * 60)
    
    # Test case 1: Valid JSON in markdown
    print("\n1. Valid JSON in Markdown:")
    output1 = """
    Here's the extracted task information:
    ```json
    {
        "version": "2.0",
        "title": "Fix authentication bug",
        "priority": 4,
        "category": "bug",
        "description": "Users cannot log in with social auth",
        "tags": ["auth", "urgent"]
    }
    ```
    """
    result1 = ValidationMiddleware.validate(output1, TaskExtractionV2)
    print(f"   Success: {result1.success}")
    if result1.success:
        print(f"   Data: {result1.data.model_dump_json(indent=2)}")
    
    # Test case 2: Valid JSON with trailing comma
    print("\n2. JSON with Trailing Comma:")
    output2 = """{
        "version": "2.0",
        "title": "Implement dashboard",
        "priority": 3,
        "category": "feature",
    }"""
    result2 = ValidationMiddleware.validate(output2, TaskExtractionV2)
    print(f"   Success: {result2.success}")
    if result2.success:
        print(f"   Data: {result2.data.model_dump_json(indent=2)}")
    
    # Test case 3: Invalid priority value
    print("\n3. Invalid Priority Value:")
    output3 = """{
        "version": "2.0",
        "title": "Update documentation",
        "priority": 10,
        "category": "docs"
    }"""
    result3 = ValidationMiddleware.validate(output3, TaskExtractionV2)
    print(f"   Success: {result3.success}")
    if not result3.success:
        print(f"   Errors:")
        for error in result3.errors:
            print(f"     - {error}")
    
    # Test case 4: Missing required field
    print("\n4. Missing Required Field:")
    output4 = """{
        "version": "2.0",
        "title": "Review code",
        "priority": 2
    }"""
    result4 = ValidationMiddleware.validate(output4, TaskExtractionV2)
    print(f"   Success: {result4.success}")
    if not result4.success:
        print(f"   Errors:")
        for error in result4.errors:
            print(f"     - {error}")
    
    # Test case 5: Not valid JSON at all
    print("\n5. Invalid JSON:")
    output5 = "This is just plain text, no JSON here!"
    result5 = ValidationMiddleware.validate(output5, TaskExtractionV2)
    print(f"   Success: {result5.success}")
    if not result5.success:
        print(f"   Errors:")
        for error in result5.errors:
            print(f"     - {error}")
    
    print("\n" + "=" * 60)
    print("Validation middleware demonstration complete!")
    print("=" * 60)


if __name__ == "__main__":
    # Import schema for demonstration
    import sys
    sys.path.insert(0, '.')
    from src.schema_definitions import TaskExtractionV2
    
    demonstrate_validation()
