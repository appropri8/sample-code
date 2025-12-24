"""Planner agent that decides what to do."""
from src.agents.base_agent import BaseAgent
from typing import Dict, Any


class PlannerAgent(BaseAgent):
    """Agent that plans the workflow steps."""
    
    def _do_process(self, message: Dict[str, Any]) -> Dict[str, Any]:
        user_request = message.get("request", "")
        
        # Agent logic: decide what to do
        plan = {
            "steps": [
                {"agent": "tool-agent", "action": "search", "query": user_request},
                {"agent": "verifier-agent", "action": "validate"},
                {"agent": "summarizer-agent", "action": "format"}
            ]
        }
        
        return {
            "plan": plan,
            "conversation_id": message.get("conversation_id"),
            "workflow_id": message.get("workflow_id")
        }

