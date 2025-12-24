"""Summarizer agent that formats output."""
from src.agents.base_agent import BaseAgent
from typing import Dict, Any


class SummarizerAgent(BaseAgent):
    """Agent that formats the final output."""
    
    def _do_process(self, message: Dict[str, Any]) -> Dict[str, Any]:
        tool_result = message.get("tool_result", {})
        validation_result = message.get("validation_result", {})
        
        # Format output
        if validation_result.get("valid"):
            formatted_output = f"Result: {tool_result.get('data', 'No data')}"
        else:
            formatted_output = f"Error: {validation_result.get('message', 'Unknown error')}"
        
        message["formatted_output"] = formatted_output
        return message

