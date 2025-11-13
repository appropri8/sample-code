"""Agent contracts define what agents can do"""

from typing import List
from dataclasses import dataclass


@dataclass
class AgentContract:
    """Defines what an agent can do"""
    name: str
    allowed_tools: List[str]
    max_runtime_seconds: int
    max_steps: int
    max_tokens: int
    max_cost_dollars: float
    required_output: str  # "text", "json", "structured"
    
    def validate_tool(self, tool_name: str) -> bool:
        """Check if tool is allowed"""
        return tool_name in self.allowed_tools

