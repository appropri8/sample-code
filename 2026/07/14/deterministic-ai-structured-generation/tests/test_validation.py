"""
Tests for validation middleware
"""

import pytest
from hypothesis import given, strategies as st
from pydantic import BaseModel, Field, ValidationError
from typing import Literal

# Import from parent
import sys
sys.path.insert(0, '..')
from src.validation_middleware import ValidationMiddleware, ValidationResult


class SimpleSchema(BaseModel):
    """Simple test schema"""
    title: str = Field(min_length=3, max_length=50)
    priority: Literal[1, 2, 3, 4, 5]


class TestJSONExtraction:
    """Test JSON extraction from various formats"""
    
    def test_clean_json(self):
        """Test extraction of clean JSON"""
        text = '{"title": "Test", "priority": 3}'
        result = ValidationMiddleware.extract_json(text)
        assert result is not None
        assert result["title"] == "Test"
        assert result["priority"] == 3
    
    def test_json_in_markdown(self):
        """Test extraction from markdown code blocks"""
        text = """Here's the result:
```json
{"title": "Test", "priority": 3}
```
"""
        result = ValidationMiddleware.extract_json(text)
        assert result is not None
        assert result["title"] == "Test"
    
    def test_json_with_trailing_comma(self):
        """Test JSON with trailing comma"""
        text = '{"title": "Test", "priority": 3,}'
        result = ValidationMiddleware.extract_json(text)
        assert result is not None
        assert result["title"] == "Test"
    
    def test_json_with_extra_text(self):
        """Test JSON with text before and after"""
        text = 'Here is the output: {"title": "Test", "priority": 3} Thanks!'
        result = ValidationMiddleware.extract_json(text)
        assert result is not None
        assert result["title"] == "Test"
    
    def test_invalid_json(self):
        """Test that invalid JSON returns None"""
        text = "This is not JSON at all"
        result = ValidationMiddleware.extract_json(text)
        assert result is None


class TestValidation:
    """Test schema validation"""
    
    def test_valid_data(self):
        """Test validation of valid data"""
        data = {"title": "Valid Task", "priority": 3}
        validated, errors = ValidationMiddleware.validate_with_details(data, SimpleSchema)
        assert validated is not None
        assert len(errors) == 0
    
    def test_missing_required_field(self):
        """Test validation with missing required field"""
        data = {"title": "Valid Task"}
        validated, errors = ValidationMiddleware.validate_with_details(data, SimpleSchema)
        assert validated is None
        assert len(errors) > 0
        assert any("priority" in error for error in errors)
    
    def test_invalid_enum(self):
        """Test validation with invalid enum value"""
        data = {"title": "Valid Task", "priority": 10}
        validated, errors = ValidationMiddleware.validate_with_details(data, SimpleSchema)
        assert validated is None
        assert len(errors) > 0
    
    def test_string_too_short(self):
        """Test validation with string too short"""
        data = {"title": "X", "priority": 3}
        validated, errors = ValidationMiddleware.validate_with_details(data, SimpleSchema)
        assert validated is None
        assert len(errors) > 0


class TestEndToEnd:
    """Test complete validation pipeline"""
    
    def test_valid_output(self):
        """Test complete pipeline with valid output"""
        output = '{"title": "Complete Task", "priority": 4}'
        result = ValidationMiddleware.validate(output, SimpleSchema)
        assert result.success
        assert result.data is not None
        assert result.data.title == "Complete Task"
    
    def test_invalid_output(self):
        """Test complete pipeline with invalid output"""
        output = '{"title": "Complete Task", "priority": 10}'
        result = ValidationMiddleware.validate(output, SimpleSchema)
        assert not result.success
        assert len(result.errors) > 0
    
    def test_unparseable_output(self):
        """Test complete pipeline with unparseable output"""
        output = "Not JSON at all"
        result = ValidationMiddleware.validate(output, SimpleSchema)
        assert not result.success
        assert any("parse" in error.lower() for error in result.errors)


# Property-based tests
@given(
    title=st.text(min_size=3, max_size=50, alphabet=st.characters(blacklist_categories=('Cs',))),
    priority=st.integers(min_value=1, max_value=5)
)
def test_valid_inputs_always_validate(title, priority):
    """Test that any valid input validates correctly"""
    data = {"title": title, "priority": priority}
    validated, errors = ValidationMiddleware.validate_with_details(data, SimpleSchema)
    assert validated is not None
    assert validated.title == title
    assert validated.priority == priority


@given(
    title=st.text(min_size=3, max_size=50, alphabet=st.characters(blacklist_categories=('Cs',))),
    priority=st.integers().filter(lambda x: x < 1 or x > 5)
)
def test_invalid_priority_always_fails(title, priority):
    """Test that invalid priority always fails validation"""
    data = {"title": title, "priority": priority}
    validated, errors = ValidationMiddleware.validate_with_details(data, SimpleSchema)
    assert validated is None
    assert len(errors) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
