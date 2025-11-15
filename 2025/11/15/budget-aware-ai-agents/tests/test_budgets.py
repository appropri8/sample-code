"""Tests for budget management."""

import time
import pytest
from src.budgets import RunBudget, BudgetManager


class TestRunBudget:
    """Tests for RunBudget dataclass."""
    
    def test_create_budget(self):
        budget = RunBudget(max_steps=10, max_tokens=5000, max_seconds=30)
        assert budget.max_steps == 10
        assert budget.max_tokens == 5000
        assert budget.max_seconds == 30
        assert budget.max_nested_tool_calls is None
    
    def test_create_budget_with_nested_calls(self):
        budget = RunBudget(
            max_steps=10,
            max_tokens=5000,
            max_seconds=30,
            max_nested_tool_calls=5
        )
        assert budget.max_nested_tool_calls == 5


class TestBudgetManager:
    """Tests for BudgetManager."""
    
    def test_initial_state(self):
        budget = RunBudget(max_steps=10, max_tokens=5000, max_seconds=30)
        manager = BudgetManager(budget)
        
        assert manager.steps_used == 0
        assert manager.tokens_used == 0
        assert manager.nested_tool_calls == 0
    
    def test_can_make_call_within_budget(self):
        budget = RunBudget(max_steps=10, max_tokens=5000, max_seconds=30)
        manager = BudgetManager(budget)
        
        assert manager.can_make_call(1000) is True
    
    def test_can_make_call_exceeds_steps(self):
        budget = RunBudget(max_steps=2, max_tokens=5000, max_seconds=30)
        manager = BudgetManager(budget)
        
        manager.record_call(100)
        manager.record_call(100)
        
        assert manager.can_make_call(100) is False
    
    def test_can_make_call_exceeds_tokens(self):
        budget = RunBudget(max_steps=10, max_tokens=1000, max_seconds=30)
        manager = BudgetManager(budget)
        
        manager.record_call(600)
        
        assert manager.can_make_call(500) is False  # Would exceed limit
        assert manager.can_make_call(400) is True   # Within limit
    
    def test_can_make_call_exceeds_time(self):
        budget = RunBudget(max_steps=10, max_tokens=5000, max_seconds=0.1)
        manager = BudgetManager(budget)
        
        time.sleep(0.15)
        
        assert manager.can_make_call(100) is False
    
    def test_can_make_call_exceeds_nested_tool_calls(self):
        budget = RunBudget(
            max_steps=10,
            max_tokens=5000,
            max_seconds=30,
            max_nested_tool_calls=2
        )
        manager = BudgetManager(budget)
        
        manager.record_call(100, is_tool_call=True)
        manager.record_call(100, is_tool_call=True)
        
        assert manager.can_make_call(100) is False
    
    def test_record_call(self):
        budget = RunBudget(max_steps=10, max_tokens=5000, max_seconds=30)
        manager = BudgetManager(budget)
        
        manager.record_call(500)
        
        assert manager.steps_used == 1
        assert manager.tokens_used == 500
    
    def test_record_tool_call(self):
        budget = RunBudget(max_steps=10, max_tokens=5000, max_seconds=30)
        manager = BudgetManager(budget)
        
        manager.record_call(500, is_tool_call=True)
        
        assert manager.steps_used == 1
        assert manager.tokens_used == 500
        assert manager.nested_tool_calls == 1
    
    def test_remaining(self):
        budget = RunBudget(max_steps=10, max_tokens=5000, max_seconds=30)
        manager = BudgetManager(budget)
        
        manager.record_call(1000)
        
        remaining = manager.remaining()
        
        assert remaining["steps"] == 9
        assert remaining["tokens"] == 4000
        assert remaining["seconds"] > 0
    
    def test_is_exhausted(self):
        budget = RunBudget(max_steps=2, max_tokens=5000, max_seconds=30)
        manager = BudgetManager(budget)
        
        assert manager.is_exhausted() is False
        
        manager.record_call(100)
        manager.record_call(100)
        
        assert manager.is_exhausted() is True

