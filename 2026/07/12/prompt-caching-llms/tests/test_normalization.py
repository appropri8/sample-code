"""
Tests for prompt normalization utilities.
"""

import pytest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from prompt_normalization import (
    normalize_whitespace,
    normalize_json,
    normalize_list,
    normalize_prompt,
    PromptBuilder
)


class TestWhitespaceNormalization:
    """Test whitespace normalization."""
    
    def test_multiple_spaces(self):
        """Test multiple spaces are reduced to single space."""
        text = "Hello    world"
        expected = "Hello world"
        assert normalize_whitespace(text) == expected
    
    def test_multiple_newlines(self):
        """Test multiple newlines are reduced to single newline."""
        text = "Hello\n\n\nworld"
        expected = "Hello\nworld"
        assert normalize_whitespace(text) == expected
    
    def test_leading_trailing_whitespace(self):
        """Test leading/trailing whitespace is removed."""
        text = "  Hello world  "
        expected = "Hello world"
        assert normalize_whitespace(text) == expected
    
    def test_line_ending_normalization(self):
        """Test different line endings are normalized."""
        text = "Hello\r\nworld\rtest"
        expected = "Hello\nworld\ntest"
        assert normalize_whitespace(text) == expected


class TestJSONNormalization:
    """Test JSON normalization."""
    
    def test_key_sorting(self):
        """Test dictionary keys are sorted."""
        data1 = {"b": 2, "a": 1, "c": 3}
        data2 = {"c": 3, "a": 1, "b": 2}
        
        assert normalize_json(data1) == normalize_json(data2)
    
    def test_consistent_formatting(self):
        """Test consistent formatting (no spaces)."""
        data = {"name": "test", "value": 123}
        result = normalize_json(data)
        
        # Should be compact (no spaces after : or ,)
        assert result == '{"name":"test","value":123}'
    
    def test_nested_objects(self):
        """Test nested objects are normalized."""
        data1 = {"outer": {"b": 2, "a": 1}}
        data2 = {"outer": {"a": 1, "b": 2}}
        
        assert normalize_json(data1) == normalize_json(data2)


class TestListNormalization:
    """Test list normalization."""
    
    def test_sorting(self):
        """Test lists are sorted."""
        list1 = ["c", "a", "b"]
        list2 = ["b", "c", "a"]
        
        assert normalize_list(list1) == normalize_list(list2)
    
    def test_no_sorting(self):
        """Test lists without sorting."""
        list1 = ["c", "a", "b"]
        list2 = ["b", "c", "a"]
        
        assert normalize_list(list1, sort=False) != normalize_list(list2, sort=False)
    
    def test_comma_separated(self):
        """Test output is comma-separated."""
        items = ["a", "b", "c"]
        result = normalize_list(items)
        
        assert result == "a, b, c"


class TestPromptNormalization:
    """Test complete prompt normalization."""
    
    def test_end_to_end(self):
        """Test complete normalization."""
        prompt1 = "You are a helpful   assistant.\n\n\nQuestion: What is Python?"
        prompt2 = "You are a helpful assistant.\n\nQuestion: What is Python?"
        prompt3 = "  You are a helpful assistant.\nQuestion: What is Python?  "
        
        # All should normalize to the same result
        normalized1 = normalize_prompt(prompt1)
        normalized2 = normalize_prompt(prompt2)
        normalized3 = normalize_prompt(prompt3)
        
        assert normalized1 == normalized2 == normalized3


class TestPromptBuilder:
    """Test prompt builder."""
    
    def test_consistent_prompts(self):
        """Test builder produces consistent prompts."""
        builder = PromptBuilder("You are a helpful assistant.")
        
        # Same query with different whitespace
        prompt1 = builder.build("What is Python?")
        prompt2 = builder.build("What  is  Python?")
        prompt3 = builder.build("  What is Python?  ")
        
        assert prompt1 == prompt2 == prompt3
    
    def test_context_normalization(self):
        """Test context is normalized."""
        builder = PromptBuilder("You are a helpful assistant.")
        
        context1 = {"user": "alice", "id": 123}
        context2 = {"id": 123, "user": "alice"}  # Different order
        
        prompt1 = builder.build("Test query", context1)
        prompt2 = builder.build("Test query", context2)
        
        assert prompt1 == prompt2
    
    def test_system_prompt_first(self):
        """Test system prompt comes first."""
        builder = PromptBuilder("System prompt here.")
        prompt = builder.build("User query", {"context": "data"})
        
        assert prompt.startswith("System prompt here.")
    
    def test_user_query_last(self):
        """Test user query comes last."""
        builder = PromptBuilder("System prompt.")
        prompt = builder.build("User query")
        
        assert prompt.endswith("Question: User query")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
