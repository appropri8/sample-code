"""Tests for validators"""

import pytest
from src.validators import (
    validate_tool_input,
    validate_required_fields,
    validate_field_types,
    validate_string_constraints,
    validate_all
)


def test_validate_required_fields():
    """Test required field validation"""
    schema = {
        "type": "object",
        "properties": {
            "ticket_id": {"type": "string"},
            "comment": {"type": "string"}
        },
        "required": ["ticket_id", "comment"]
    }
    
    # Missing required field
    errors = validate_required_fields(schema, {"ticket_id": "TKT-123"})
    assert len(errors) > 0
    assert any("comment" in error for error in errors)
    
    # All required fields present
    errors = validate_required_fields(schema, {"ticket_id": "TKT-123", "comment": "Test"})
    assert len(errors) == 0


def test_validate_field_types():
    """Test field type validation"""
    schema = {
        "type": "object",
        "properties": {
            "ticket_id": {"type": "string"},
            "count": {"type": "integer"}
        }
    }
    
    # Wrong type
    errors = validate_field_types(schema, {"ticket_id": 123})
    assert len(errors) > 0
    
    # Correct types
    errors = validate_field_types(schema, {"ticket_id": "TKT-123", "count": 5})
    assert len(errors) == 0


def test_validate_string_constraints():
    """Test string constraint validation"""
    schema = {
        "type": "object",
        "properties": {
            "comment": {
                "type": "string",
                "minLength": 10,
                "maxLength": 100
            }
        }
    }
    
    # Too short
    errors = validate_string_constraints(schema, {"comment": "short"})
    assert len(errors) > 0
    
    # Too long
    errors = validate_string_constraints(schema, {"comment": "x" * 101})
    assert len(errors) > 0
    
    # Valid length
    errors = validate_string_constraints(schema, {"comment": "This is a valid comment"})
    assert len(errors) == 0


def test_validate_all():
    """Test comprehensive validation"""
    schema = {
        "type": "object",
        "properties": {
            "ticket_id": {"type": "string"},
            "comment": {
                "type": "string",
                "minLength": 10
            }
        },
        "required": ["ticket_id", "comment"]
    }
    
    # Missing required field
    result = validate_all(schema, {"ticket_id": "TKT-123"})
    assert result["valid"] is False
    assert len(result["errors"]) > 0
    
    # Valid input
    result = validate_all(schema, {
        "ticket_id": "TKT-123",
        "comment": "This is a valid comment"
    })
    assert result["valid"] is True
    assert len(result["errors"]) == 0

