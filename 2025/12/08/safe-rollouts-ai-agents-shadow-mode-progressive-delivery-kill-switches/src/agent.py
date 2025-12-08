"""Simple agent implementation for demonstration."""

import time
from typing import List, Dict, Any, Optional
from .agent_config import AgentConfig


class Agent:
    """Simple agent that processes messages and calls tools."""
    
    def __init__(self, config: AgentConfig):
        """
        Initialize agent from config.
        
        Args:
            config: Agent configuration
        """
        self.config = config
        self.version = config.version
        self.model_provider = config.model["provider"]
        self.model_name = config.model["name"]
        self.system_prompt = config.prompt["system"]
        self.tools = [t["name"] for t in config.tools if t.get("enabled", True)]
        self.max_steps = config.policies.get("max_steps", 10)
        self.max_cost = config.policies.get("max_cost_per_request", 1.0)
    
    def process(self, user_message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a user message and return response.
        
        Args:
            user_message: The user's message
            context: Optional context (conversation history, user data, etc.)
        
        Returns:
            Response dictionary with tool_calls, response, cost, latency, etc.
        """
        start_time = time.time()
        
        # Simulate agent processing
        # In real implementation, this would call an LLM
        
        tool_calls = []
        cost = 0.0
        policy_violations = []
        
        # Simple rule-based processing for demonstration
        message_lower = user_message.lower()
        
        if "search" in message_lower or "find" in message_lower:
            tool_calls.append({
                "tool_name": "search_database",
                "parameters": {"query": user_message}
            })
            cost += 0.10
        
        if "email" in message_lower or "send" in message_lower:
            tool_calls.append({
                "tool_name": "send_email",
                "parameters": {"to": "user@example.com", "subject": "Notification"}
            })
            cost += 0.05
        
        # Check policy violations
        if len(tool_calls) > self.max_steps:
            policy_violations.append(f"Exceeded max_steps: {len(tool_calls)} > {self.max_steps}")
        
        if cost > self.max_cost:
            policy_violations.append(f"Exceeded max_cost: {cost} > {self.max_cost}")
        
        latency_ms = (time.time() - start_time) * 1000
        
        # Generate response (simplified)
        response_text = f"Processed your request using {len(tool_calls)} tool(s)."
        
        return {
            "version": self.version,
            "tool_calls": tool_calls,
            "response": response_text,
            "cost": cost,
            "latency_ms": latency_ms,
            "policy_violations": len(policy_violations),
            "error": len(policy_violations) > 0,
            "step_count": len(tool_calls)
        }


def create_agent(agent_name: str, version: str) -> Agent:
    """
    Create an agent instance from a versioned config.
    
    Args:
        agent_name: Name of the agent
        version: Version string (e.g., "v1.3.2")
    
    Returns:
        Agent instance
    """
    config = AgentConfig.load(agent_name, version)
    return Agent(config)
