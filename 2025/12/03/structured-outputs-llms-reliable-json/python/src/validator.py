"""Validate JSON against Pydantic schemas."""
import json
from typing import Type, TypeVar
from pydantic import BaseModel, ValidationError

T = TypeVar('T', bound=BaseModel)


def validate_json(
    json_data: dict,
    schema: Type[T]
) -> T:
    """
    Validate JSON data against a Pydantic schema.
    
    Args:
        json_data: JSON data to validate
        schema: Pydantic model class
    
    Returns:
        Validated model instance
    
    Raises:
        ValueError: If validation fails
    """
    try:
        return schema.model_validate(json_data)
    except ValidationError as e:
        # Format errors for better readability
        errors = []
        for error in e.errors():
            field_path = ".".join(str(loc) for loc in error["loc"])
            errors.append({
                "field": field_path,
                "message": error["msg"],
                "type": error["type"],
                "input": error.get("input")
            })
        
        error_msg = f"Validation failed: {json.dumps(errors, indent=2)}"
        raise ValueError(error_msg) from e


def format_validation_error(error: ValidationError) -> str:
    """
    Format a ValidationError into a readable string.
    
    Args:
        error: ValidationError instance
    
    Returns:
        Formatted error message
    """
    errors = []
    for err in error.errors():
        field_path = ".".join(str(loc) for loc in err["loc"])
        errors.append(f"{field_path}: {err['msg']}")
    
    return "; ".join(errors)

