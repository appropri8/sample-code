"""Tests for repair loop functionality."""

import pytest
from src.repair_loop import repair_loop, safe_extract, build_repair_prompt
from src.schemas import CustomerExtraction, TicketClassification


class TestRepairLoop:
    """Test repair loop with retry logic."""
    
    def test_repair_loop_succeeds_first_try(self):
        """Test repair loop succeeds when first response is valid."""
        def mock_llm(prompt):
            return '{"name": "John Doe", "email": "john@example.com", "priority": 3, "tags": []}'
        
        result = repair_loop(
            "Extract customer info",
            CustomerExtraction,
            llm_call=mock_llm,
            max_retries=2
        )
        
        assert result is not None
        assert result.name == "John Doe"
        assert result.email == "john@example.com"
    
    def test_repair_loop_repairs_on_second_try(self):
        """Test repair loop fixes errors on retry."""
        call_count = [0]
        
        def mock_llm(prompt):
            call_count[0] += 1
            if call_count[0] == 1:
                # First call: missing email
                return '{"name": "John Doe", "priority": 3}'
            else:
                # Second call: fixed
                return '{"name": "John Doe", "email": "john@example.com", "priority": 3, "tags": []}'
        
        result = repair_loop(
            "Extract customer info",
            CustomerExtraction,
            llm_call=mock_llm,
            max_retries=2
        )
        
        assert result is not None
        assert result.email == "john@example.com"
        assert call_count[0] == 2
    
    def test_repair_loop_fails_after_max_retries(self):
        """Test repair loop fails after max retries."""
        def mock_llm(prompt):
            # Always return invalid (missing email)
            return '{"name": "John Doe", "priority": 3}'
        
        result = repair_loop(
            "Extract customer info",
            CustomerExtraction,
            llm_call=mock_llm,
            max_retries=2
        )
        
        assert result is None
    
    def test_safe_extract_with_fallback(self):
        """Test safe_extract uses fallback on failure."""
        def mock_llm(prompt):
            return '{"name": "Invalid", "priority": 3}'  # Missing email
        
        fallback = CustomerExtraction(
            name="Fallback User",
            email="fallback@example.com",
            priority=1
        )
        
        result = safe_extract(
            "Extract customer info",
            CustomerExtraction,
            llm_call=mock_llm,
            fallback=fallback
        )
        
        assert result.email == "fallback@example.com"
    
    def test_safe_extract_raises_without_fallback(self):
        """Test safe_extract raises error without fallback."""
        def mock_llm(prompt):
            return '{"name": "Invalid", "priority": 3}'  # Missing email
        
        with pytest.raises(ValueError, match="Failed to extract"):
            safe_extract(
                "Extract customer info",
                CustomerExtraction,
                llm_call=mock_llm,
                fallback=None
            )
    
    def test_build_repair_prompt(self):
        """Test repair prompt includes errors and schema."""
        prompt = build_repair_prompt(
            "Original request",
            "email: Field required",
            CustomerExtraction
        )
        
        assert "validation errors" in prompt.lower()
        assert "email" in prompt.lower()
        assert "original request" in prompt.lower()
        assert "schema" in prompt.lower()
