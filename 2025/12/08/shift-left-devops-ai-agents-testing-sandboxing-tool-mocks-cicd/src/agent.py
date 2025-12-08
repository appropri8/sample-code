"""Simple agent implementation for demonstration."""

from typing import List, Dict, Any, Optional
from .tools import create_tools
from .contract_validator import validate_agent_action, check_policy_violations


class Agent:
    """Simple agent that processes messages and calls tools."""
    
    def __init__(self, tools: Optional[Dict[str, Any]] = None, use_mocks: bool = False):
        """
        Initialize agent.
        
        Args:
            tools: Dictionary of tool instances (if None, creates based on use_mocks)
            use_mocks: Whether to use mock tools
        """
        if tools is None:
            self.tools = create_tools(use_mocks=use_mocks)
        else:
            self.tools = tools
        
        self.tool_calls_history = []
        self.step_count = 0
    
    def process(self, user_message: str, max_steps: int = 10) -> Dict[str, Any]:
        """
        Process a user message and return response.
        
        Args:
            user_message: The user's message
            max_steps: Maximum number of tool calls allowed
        
        Returns:
            Response dictionary with tool_calls and final_message
        """
        self.tool_calls_history = []
        self.step_count = 0
        
        # Simple rule-based agent (in real implementation, would use LLM)
        # This is a simplified version for demonstration
        
        tool_calls = []
        
        # Simple intent detection
        message_lower = user_message.lower()
        
        if "search" in message_lower or "find" in message_lower:
            # Extract query
            query = user_message.replace("search", "").replace("find", "").strip()
            if not query:
                query = "default search"
            
            action = {
                "tool_name": "search_database",
                "parameters": {"query": query, "limit": 10}
            }
            
            # Validate action
            is_valid, errors = validate_agent_action(action)
            if not is_valid:
                return {
                    "tool_calls": [],
                    "final_message": f"Error: {', '.join(errors)}",
                    "step_count": self.step_count,
                    "errors": errors
                }
            
            # Call tool
            results = self.tools["database"].search(query, limit=10)
            tool_calls.append({
                "tool_name": "search_database",
                "parameters": {"query": query, "limit": 10},
                "results": results
            })
            self.step_count += 1
        
        elif "email" in message_lower or "send" in message_lower:
            # Extract email details (simplified)
            action = {
                "tool_name": "send_notification",
                "parameters": {
                    "query": user_message,  # Simplified
                    "email": "user@example.com"  # Would extract from message
                }
            }
            
            is_valid, errors = validate_agent_action(action)
            if not is_valid:
                return {
                    "tool_calls": [],
                    "final_message": f"Error: {', '.join(errors)}",
                    "step_count": self.step_count,
                    "errors": errors
                }
            
            # Call tool
            result = self.tools["email"].send_email(
                to="user@example.com",
                subject="Notification",
                body=user_message
            )
            tool_calls.append({
                "tool_name": "send_notification",
                "parameters": action["parameters"],
                "results": result
            })
            self.step_count += 1
        
        # Check policy violations
        violations = check_policy_violations(
            [tc for tc in tool_calls],
            environment="test" if self.tools.get("database").__class__.__name__.startswith("Mock") else "prod"
        )
        
        if violations:
            return {
                "tool_calls": tool_calls,
                "final_message": f"Policy violations: {', '.join(violations)}",
                "step_count": self.step_count,
                "errors": violations
            }
        
        self.tool_calls_history = tool_calls
        
        return {
            "tool_calls": tool_calls,
            "final_message": "Request processed successfully",
            "step_count": self.step_count,
            "errors": []
        }


def create_agent(use_mocks: bool = False) -> Agent:
    """
    Create an agent instance.
    
    Args:
        use_mocks: Whether to use mock tools
    
    Returns:
        Agent instance
    """
    return Agent(use_mocks=use_mocks)
