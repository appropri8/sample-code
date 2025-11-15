"""Budget management for AI agents."""

import time
from dataclasses import dataclass
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class RunBudget:
    """Budget limits for a single agent run."""
    max_steps: int
    max_tokens: int
    max_seconds: float
    max_nested_tool_calls: Optional[int] = None


class BudgetManager:
    """Manages budget tracking and enforcement for agent runs."""
    
    def __init__(self, budget: RunBudget):
        self.budget = budget
        self.steps_used = 0
        self.tokens_used = 0
        self.start_time = time.time()
        self.nested_tool_calls = 0
    
    def can_make_call(self, estimated_tokens: int) -> bool:
        """Check if we can make another call within budget."""
        if self.steps_used >= self.budget.max_steps:
            return False
        
        if self.tokens_used + estimated_tokens > self.budget.max_tokens:
            return False
        
        elapsed = time.time() - self.start_time
        if elapsed >= self.budget.max_seconds:
            return False
        
        if self.budget.max_nested_tool_calls:
            if self.nested_tool_calls >= self.budget.max_nested_tool_calls:
                return False
        
        return True
    
    def record_call(self, tokens_used: int, is_tool_call: bool = False, step_type: str = "model"):
        """Record a model or tool call with logging."""
        self.steps_used += 1
        self.tokens_used += tokens_used
        if is_tool_call:
            self.nested_tool_calls += 1
        
        # Log metrics
        logger.info({
            "event": "agent_step",
            "step_type": step_type,
            "tokens_used": tokens_used,
            "total_tokens": self.tokens_used,
            "steps_used": self.steps_used,
            "nested_tool_calls": self.nested_tool_calls,
            "budget_exhausted": self.is_exhausted()
        })
    
    def remaining(self) -> Dict[str, float]:
        """Get remaining budget."""
        elapsed = time.time() - self.start_time
        remaining = {
            "steps": self.budget.max_steps - self.steps_used,
            "tokens": self.budget.max_tokens - self.tokens_used,
            "seconds": self.budget.max_seconds - elapsed,
        }
        
        if self.budget.max_nested_tool_calls:
            remaining["nested_tool_calls"] = (
                self.budget.max_nested_tool_calls - self.nested_tool_calls
            )
        
        return remaining
    
    def is_exhausted(self) -> bool:
        """Check if budget is exhausted."""
        remaining = self.remaining()
        return (
            remaining["steps"] <= 0 or
            remaining["tokens"] <= 0 or
            remaining["seconds"] <= 0
        )

