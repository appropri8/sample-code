"""Tests for JSON extraction and validation."""

import pytest
from src.validator import extract_json, validate_output
from src.schemas import CustomerExtraction, TicketClassification


class TestExtractJson:
    """Test JSON extraction from text."""
    
    def test_extract_clean_json(self):
        """Test extracting clean JSON."""
        text = '{"name": "John", "email": "john@example.com"}'
        result = extract_json(text)
        assert result == {"name": "John", "email": "john@example.com"}
    
    def test_extract_json_with_markdown(self):
        """Test extracting JSON from markdown code block."""
        text = '```json\n{"name": "John", "email": "john@example.com"}\n```'
        result = extract_json(text)
        assert result == {"name": "John", "email": "john@example.com"}
    
    def test_extract_json_with_extra_text(self):
        """Test extracting JSON with extra text around it."""
        text = 'Here is the JSON: {"name": "John", "email": "john@example.com"} That\'s it.'
        result = extract_json(text)
        assert result == {"name": "John", "email": "john@example.com"}
    
    def test_extract_json_with_trailing_comma(self):
        """Test extracting JSON with trailing comma (should be fixed)."""
        text = '{"name": "John", "email": "john@example.com",}'
        result = extract_json(text)
        assert result == {"name": "John", "email": "john@example.com"}
    
    def test_extract_json_fails_on_invalid(self):
        """Test that invalid JSON returns None."""
        text = 'This is not JSON at all'
        result = extract_json(text)
        assert result is None


class TestValidateOutput:
    """Test validation against schemas."""
    
    def test_validate_valid_customer(self):
        """Test validating valid customer extraction."""
        data = {
            "name": "John Doe",
            "email": "john@example.com",
            "priority": 3,
            "tags": ["vip"]
        }
        model, error = validate_output(data, CustomerExtraction)
        assert model is not None
        assert error is None
        assert model.name == "John Doe"
        assert model.email == "john@example.com"
        assert model.priority == 3
    
    def test_validate_missing_required_field(self):
        """Test validation fails on missing required field."""
        data = {
            "name": "John Doe",
            # Missing email
            "priority": 3
        }
        model, error = validate_output(data, CustomerExtraction)
        assert model is None
        assert error is not None
        assert "email" in error.lower()
        assert "required" in error.lower()
    
    def test_validate_wrong_type(self):
        """Test validation fails on wrong type."""
        data = {
            "name": "John Doe",
            "email": "john@example.com",
            "priority": "high"  # Should be integer 1-5
        }
        model, error = validate_output(data, CustomerExtraction)
        assert model is None
        assert error is not None
        assert "priority" in error.lower()
    
    def test_validate_invalid_enum(self):
        """Test validation fails on invalid enum value."""
        data = {
            "intent": "invalid_intent",  # Not in allowed values
            "priority": "low"
        }
        model, error = validate_output(data, TicketClassification)
        assert model is None
        assert error is not None
        assert "intent" in error.lower()
    
    def test_validate_invalid_email(self):
        """Test validation fails on invalid email format."""
        data = {
            "name": "John Doe",
            "email": "not-an-email",  # Invalid format
            "priority": 3
        }
        model, error = validate_output(data, CustomerExtraction)
        assert model is None
        assert error is not None
        assert "email" in error.lower()
    
    def test_validate_error_path_formatting(self):
        """Test that error messages include proper paths."""
        data = {
            "name": "John Doe",
            "email": "john@example.com",
            "priority": 10  # Out of range
        }
        model, error = validate_output(data, CustomerExtraction)
        assert model is None
        assert error is not None
        # Error should mention the field path
        assert "priority" in error
