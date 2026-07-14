"""
Validation Middleware - Reusable validation wrapper

Handles:
- JSON parsing from LLM output
- Schema validation
- Detailed error reporting
- Common edge cases
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
                elif "enum" in error_type or "literal" in error_type:
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
