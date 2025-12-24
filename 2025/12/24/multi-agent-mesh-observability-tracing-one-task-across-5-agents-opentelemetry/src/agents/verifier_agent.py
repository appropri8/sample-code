"""Verifier agent that validates results."""
from src.agents.base_agent import BaseAgent
from typing import Dict, Any


class VerifierAgent(BaseAgent):
    """Agent that verifies tool results."""
    
    def _do_process(self, message: Dict[str, Any]) -> Dict[str, Any]:
        tool_result = message.get("tool_result", {})
        
        # Validation logic
        is_valid = tool_result.get("status") == "success"
        
        message["validation_result"] = {
            "valid": is_valid,
            "message": "Validation passed" if is_valid else "Validation failed"
        }
        
        return message

