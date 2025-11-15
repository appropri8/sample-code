"""Example support agent with policy layer"""

from typing import Dict, Any, List, Optional
import uuid
from datetime import datetime

from .policy_layer import PolicyLayer
from .tool_registry import get_tools_for_role


class SupportAgent:
    """Example support agent that uses tools safely"""
    
    def __init__(self, user_role: str, user_id: str):
        self.user_role = user_role
        self.user_id = user_id
        self.policy = PolicyLayer(user_role, user_id)
        self.run_id = f"run_{uuid.uuid4().hex[:8]}"
        self.tool_results: List[Dict[str, Any]] = []
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tools for this agent"""
        tools = get_tools_for_role(self.user_role)
        return [tool.name for tool in tools]
    
    def call_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool through the policy layer"""
        result = self.policy.call_tool_with_policy(
            tool_name=tool_name,
            args=args,
            run_id=self.run_id
        )
        
        if result["status"] == "success":
            self.tool_results.append({
                "tool": tool_name,
                "result": result.get("result")
            })
        elif result["status"] == "approval_required":
            self.tool_results.append({
                "tool": tool_name,
                "status": "approval_required",
                "approval_id": result.get("approval_id"),
                "message": result.get("message")
            })
        
        return result
    
    def handle_user_request(self, user_input: str) -> Dict[str, Any]:
        """
        Handle a user request
        
        This is a simplified example. In a real implementation,
        you would use an LLM to decide which tools to call.
        """
        # Simulate agent deciding to read a ticket
        if "ticket" in user_input.lower() and "read" in user_input.lower():
            # Extract ticket ID (simplified)
            ticket_id = self._extract_ticket_id(user_input) or "TKT-12345"
            result = self.call_tool("read_ticket", {"ticket_id": ticket_id})
            return result
        
        # Simulate agent deciding to add a comment
        if "comment" in user_input.lower() or "reply" in user_input.lower():
            ticket_id = self._extract_ticket_id(user_input) or "TKT-12345"
            comment = self._extract_comment(user_input) or "Agent response"
            result = self.call_tool("add_comment", {
                "ticket_id": ticket_id,
                "comment": comment
            })
            return result
        
        # Simulate agent deciding to close a ticket
        if "close" in user_input.lower():
            ticket_id = self._extract_ticket_id(user_input) or "TKT-12345"
            reason = self._extract_reason(user_input) or "Resolved by agent"
            result = self.call_tool("close_ticket", {
                "ticket_id": ticket_id,
                "reason": reason
            })
            return result
        
        return {
            "status": "error",
            "error": "Could not understand request",
            "suggestion": "Try: 'read ticket TKT-12345' or 'add comment to TKT-12345'"
        }
    
    def _extract_ticket_id(self, text: str) -> Optional[str]:
        """Extract ticket ID from text (simplified)"""
        # Simple pattern matching
        import re
        match = re.search(r'TKT-?\d+', text.upper())
        if match:
            return match.group(0)
        return None
    
    def _extract_comment(self, text: str) -> Optional[str]:
        """Extract comment from text (simplified)"""
        # Remove command words
        words_to_remove = ["add", "comment", "reply", "to", "ticket"]
        words = text.split()
        filtered = [w for w in words if w.lower() not in words_to_remove]
        return " ".join(filtered) if filtered else None
    
    def _extract_reason(self, text: str) -> Optional[str]:
        """Extract reason from text (simplified)"""
        # Remove command words
        words_to_remove = ["close", "ticket"]
        words = text.split()
        filtered = [w for w in words if w.lower() not in words_to_remove]
        return " ".join(filtered) if filtered else None
    
    def get_pending_approvals(self) -> List[Dict[str, Any]]:
        """Get pending approvals for this agent's run"""
        approvals = self.policy.get_pending_approvals()
        return [a.to_dict() for a in approvals if a.run_id == self.run_id]
    
    def approve_action(self, approval_id: str, reviewer_id: str) -> Dict[str, Any]:
        """Approve an action"""
        return self.policy.approve_action(approval_id, reviewer_id)
    
    def reject_action(self, approval_id: str, reviewer_id: str, reason: str) -> Dict[str, Any]:
        """Reject an action"""
        return self.policy.reject_action(approval_id, reviewer_id, reason)

