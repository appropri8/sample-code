"""Tests for token utilities."""

import pytest
from src.token_utils import estimate_tokens, count_tokens


class TestTokenUtils:
    """Tests for token estimation utilities."""
    
    def test_estimate_tokens(self):
        text = "This is a test string with some words."
        tokens = estimate_tokens(text)
        
        # Rough estimate: 1 token ≈ 4 characters
        expected = len(text) // 4
        assert tokens == expected
    
    def test_estimate_tokens_empty(self):
        assert estimate_tokens("") == 0
    
    def test_estimate_tokens_long_text(self):
        text = "a" * 1000
        tokens = estimate_tokens(text)
        
        assert tokens == 250  # 1000 / 4
    
    def test_count_tokens(self):
        # count_tokens is an alias for estimate_tokens
        text = "Test text"
        assert count_tokens(text) == estimate_tokens(text)

