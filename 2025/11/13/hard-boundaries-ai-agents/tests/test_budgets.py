"""Tests for token and cost budgets"""

import pytest
from src.budgets import TokenBudget, CostBudget, TokenBudgetExceeded, CostBudgetExceeded


def test_token_budget():
    """Test token budget"""
    budget = TokenBudget(max_tokens=100)
    
    text = "This is a test"
    tokens = budget.count_tokens(text)
    
    assert tokens > 0
    assert budget.check(text) is True
    assert budget.remaining() == 100
    
    budget.add_tokens(50)
    assert budget.tokens_used == 50
    assert budget.remaining() == 50
    
    budget.add_tokens(50)
    assert budget.tokens_used == 100
    assert budget.remaining() == 0
    
    with pytest.raises(TokenBudgetExceeded):
        budget.add_tokens(1)


def test_cost_budget():
    """Test cost budget"""
    budget = CostBudget(max_cost_dollars=1.0)
    
    # Add some cost
    budget.add_cost("gpt-4", 1000, 500)
    assert budget.cost_used > 0
    assert budget.remaining() < 1.0
    
    # Exceed budget
    budget.add_cost("gpt-4", 10000, 5000)
    
    with pytest.raises(CostBudgetExceeded):
        budget.add_cost("gpt-4", 10000, 5000)


def test_unknown_model():
    """Test unknown model handling"""
    budget = CostBudget(max_cost_dollars=1.0)
    
    with pytest.raises(ValueError):
        budget.add_cost("unknown-model", 1000, 500)

