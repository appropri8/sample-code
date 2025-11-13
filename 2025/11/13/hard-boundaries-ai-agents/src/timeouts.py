"""Time and step limits for agents"""

import signal
import time
from contextlib import contextmanager
from typing import Optional


class TimeoutError(Exception):
    """Raised when operation exceeds timeout"""
    pass


class StepLimitExceeded(Exception):
    """Raised when step limit is exceeded"""
    pass


@contextmanager
def timeout(seconds: int):
    """Kill operation after timeout"""
    def timeout_handler(signum, frame):
        raise TimeoutError(f"Operation exceeded {seconds} seconds")
    
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)


class StepBudget:
    """Track and enforce step limits"""
    def __init__(self, max_steps: int):
        self.max_steps = max_steps
        self.steps_taken = 0
    
    def check(self) -> bool:
        """Check if more steps are allowed"""
        return self.steps_taken < self.max_steps
    
    def use_step(self):
        """Record a step"""
        self.steps_taken += 1
        if not self.check():
            raise StepLimitExceeded(f"Exceeded {self.max_steps} steps")
    
    def remaining(self) -> int:
        """Get remaining steps"""
        return max(0, self.max_steps - self.steps_taken)


def call_tool_with_timeout(tool_name: str, params: dict, timeout_seconds: int = 5):
    """Call tool with timeout"""
    def call_tool(name: str, p: dict):
        # Mock tool call - replace with actual implementation
        time.sleep(0.1)  # Simulate work
        return {"result": f"Tool {name} completed", "params": p}
    
    try:
        with timeout(timeout_seconds):
            return call_tool(tool_name, params)
    except TimeoutError:
        return {"error": f"Tool {tool_name} timed out after {timeout_seconds}s"}

