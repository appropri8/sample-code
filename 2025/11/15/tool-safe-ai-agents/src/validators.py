"""Schema validation for tool inputs"""

import jsonschema
from typing import Dict, Any, List, Optional


def validate_tool_input(tool_schema: Dict[str, Any], args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate tool input against JSON schema
    
    Returns:
        {
            "valid": bool,
            "errors": List[str]
        }
    """
    try:
        jsonschema.validate(instance=args, schema=tool_schema)
        return {"valid": True, "errors": []}
    except jsonschema.ValidationError as e:
        return {
            "valid": False,
            "errors": [str(e)]
        }
    except jsonschema.SchemaError as e:
        return {
            "valid": False,
            "errors": [f"Schema error: {str(e)}"]
        }


def validate_required_fields(schema: Dict[str, Any], args: Dict[str, Any]) -> List[str]:
    """Validate required fields are present"""
    required = schema.get("required", [])
    missing = []
    
    for field in required:
        if field not in args:
            missing.append(f"Missing required field: {field}")
    
    return missing


def validate_field_types(schema: Dict[str, Any], args: Dict[str, Any]) -> List[str]:
    """Validate field types match schema"""
    errors = []
    properties = schema.get("properties", {})
    
    for field, value in args.items():
        if field in properties:
            prop = properties[field]
            expected_type = prop.get("type")
            
            if expected_type == "string" and not isinstance(value, str):
                errors.append(f"{field} must be a string, got {type(value).__name__}")
            elif expected_type == "integer" and not isinstance(value, int):
                errors.append(f"{field} must be an integer, got {type(value).__name__}")
            elif expected_type == "number" and not isinstance(value, (int, float)):
                errors.append(f"{field} must be a number, got {type(value).__name__}")
            elif expected_type == "boolean" and not isinstance(value, bool):
                errors.append(f"{field} must be a boolean, got {type(value).__name__}")
            elif expected_type == "array" and not isinstance(value, list):
                errors.append(f"{field} must be an array, got {type(value).__name__}")
            elif expected_type == "object" and not isinstance(value, dict):
                errors.append(f"{field} must be an object, got {type(value).__name__}")
    
    return errors


def validate_string_constraints(schema: Dict[str, Any], args: Dict[str, Any]) -> List[str]:
    """Validate string constraints (minLength, maxLength)"""
    errors = []
    properties = schema.get("properties", {})
    
    for field, value in args.items():
        if field in properties and isinstance(value, str):
            prop = properties[field]
            
            if "minLength" in prop:
                if len(value) < prop["minLength"]:
                    errors.append(
                        f"{field} must be at least {prop['minLength']} characters"
                    )
            
            if "maxLength" in prop:
                if len(value) > prop["maxLength"]:
                    errors.append(
                        f"{field} must be at most {prop['maxLength']} characters"
                    )
    
    return errors


def validate_all(tool_schema: Dict[str, Any], args: Dict[str, Any]) -> Dict[str, Any]:
    """Run all validations"""
    all_errors = []
    
    # Check required fields
    all_errors.extend(validate_required_fields(tool_schema, args))
    
    # Check types
    all_errors.extend(validate_field_types(tool_schema, args))
    
    # Check string constraints
    all_errors.extend(validate_string_constraints(tool_schema, args))
    
    # Use jsonschema for comprehensive validation
    jsonschema_result = validate_tool_input(tool_schema, args)
    if not jsonschema_result["valid"]:
        all_errors.extend(jsonschema_result["errors"])
    
    return {
        "valid": len(all_errors) == 0,
        "errors": all_errors
    }

