"""Token and cost budgets for agents"""

import tiktoken
from typing import Dict


# Pricing per 1K tokens (example)
PRICING = {
    "gpt-4": {"input": 0.03, "output": 0.06},
    "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002}
}


class TokenBudgetExceeded(Exception):
    """Raised when token budget is exceeded"""
    pass


class CostBudgetExceeded(Exception):
    """Raised when cost budget is exceeded"""
    pass


class TokenBudget:
    """Track and enforce token limits"""
    def __init__(self, max_tokens: int, model: str = "gpt-4"):
        self.max_tokens = max_tokens
        self.tokens_used = 0
        self.encoding = tiktoken.encoding_for_model(model)
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        return len(self.encoding.encode(text))
    
    def add_tokens(self, tokens: int):
        """Add tokens to budget"""
        self.tokens_used += tokens
        if self.tokens_used > self.max_tokens:
            raise TokenBudgetExceeded(
                f"Exceeded {self.max_tokens} tokens (used {self.tokens_used})"
            )
    
    def check(self, text: str) -> bool:
        """Check if text would exceed budget"""
        tokens_needed = self.count_tokens(text)
        return (self.tokens_used + tokens_needed) <= self.max_tokens
    
    def remaining(self) -> int:
        """Get remaining tokens"""
        return max(0, self.max_tokens - self.tokens_used)


class CostBudget:
    """Track and enforce cost limits"""
    def __init__(self, max_cost_dollars: float):
        self.max_cost_dollars = max_cost_dollars
        self.cost_used = 0.0
    
    def add_cost(self, model: str, input_tokens: int, output_tokens: int):
        """Add cost to budget"""
        if model not in PRICING:
            raise ValueError(f"Unknown model: {model}")
        
        input_cost = (input_tokens / 1000) * PRICING[model]["input"]
        output_cost = (output_tokens / 1000) * PRICING[model]["output"]
        total_cost = input_cost + output_cost
        
        self.cost_used += total_cost
        
        if self.cost_used > self.max_cost_dollars:
            raise CostBudgetExceeded(
                f"Exceeded ${self.max_cost_dollars} budget (used ${self.cost_used:.2f})"
            )
    
    def remaining(self) -> float:
        """Get remaining budget"""
        return max(0, self.max_cost_dollars - self.cost_used)


def estimate_workflow_cost(workflow_steps: list) -> Dict:
    """Estimate cost range for workflow"""
    min_cost = 0.0
    max_cost = 0.0
    
    for step in workflow_steps:
        # Estimate based on step type
        if step.get("type") == "llm_call":
            min_cost += 0.01  # Minimal prompt
            max_cost += 0.10  # Large context
        elif step.get("type") == "tool_call":
            min_cost += 0.0  # Free tool
            max_cost += 0.05  # Expensive API
    
    return {
        "min_cost": min_cost,
        "max_cost": max_cost,
        "estimated_cost": (min_cost + max_cost) / 2
    }

