"""Tests for timeouts and step budgets"""

import pytest
import time
from src.timeouts import StepBudget, StepLimitExceeded, timeout, TimeoutError


def test_step_budget():
    """Test step budget"""
    budget = StepBudget(max_steps=5)
    
    assert budget.check() is True
    assert budget.remaining() == 5
    
    for i in range(5):
        budget.use_step()
        assert budget.steps_taken == i + 1
    
    assert budget.check() is False
    assert budget.remaining() == 0
    
    with pytest.raises(StepLimitExceeded):
        budget.use_step()


def test_timeout():
    """Test timeout"""
    def fast_operation():
        time.sleep(0.1)
        return "done"
    
    # Should complete
    with timeout(1):
        result = fast_operation()
        assert result == "done"
    
    # Should timeout
    def slow_operation():
        time.sleep(2)
        return "done"
    
    with pytest.raises(TimeoutError):
        with timeout(1):
            slow_operation()

