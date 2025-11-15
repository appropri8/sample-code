"""Policy layer that wraps tool calls with guardrails"""

from typing import Dict, Any, List, Optional
import json
from datetime import datetime
import uuid

from .tool_registry import get_tool, is_tool_allowed, TOOL_REGISTRY
from .validators import validate_all
from .approvals import ApprovalQueue, ApprovalRequest


class PolicyLayer:
    """Policy layer that enforces guardrails on tool calls"""
    
    def __init__(self, user_role: str, user_id: str):
        self.user_role = user_role
        self.user_id = user_id
        self.approval_queue = ApprovalQueue()
        self.tool_call_logs: List[Dict[str, Any]] = []
    
    def call_tool_with_policy(
        self,
        tool_name: str,
        args: Dict[str, Any],
        run_id: str
    ) -> Dict[str, Any]:
        """
        Call a tool with policy checks
        
        Returns:
            {
                "status": "success" | "error" | "approval_required",
                "result": {...} | None,
                "error": str | None,
                "approval_id": str | None
            }
        """
        # Check if tool exists
        tool = get_tool(tool_name)
        if not tool:
            return {
                "status": "error",
                "error": f"Tool {tool_name} not found",
                "allowed_tools": list(TOOL_REGISTRY.keys()),
                "suggestion": f"Available tools: {', '.join(TOOL_REGISTRY.keys())}"
            }
        
        # Check role permission
        if not is_tool_allowed(tool_name, self.user_role):
            safer_alternatives = self._get_safer_alternatives(tool_name)
            return {
                "status": "error",
                "error": f"Role {self.user_role} not allowed for {tool_name}",
                "allowed_roles": tool.allowed_roles,
                "suggestion": f"Use one of these tools instead: {', '.join(safer_alternatives)}"
            }
        
        # Validate schema
        validation_result = validate_all(tool.schema, args)
        if not validation_result["valid"]:
            return {
                "status": "error",
                "error": "Validation failed",
                "details": validation_result["errors"],
                "suggestion": "Check the tool schema for required fields and types"
            }
        
        # Check if approval needed
        if tool.requires_approval:
            approval_request = self._request_approval(tool_name, args, run_id)
            return {
                "status": "approval_required",
                "approval_id": approval_request.approval_id,
                "message": "This action requires approval",
                "summary": self._format_approval_summary(tool_name, args)
            }
        
        # Execute tool
        return self._execute_tool(tool_name, args, run_id)
    
    def _request_approval(
        self,
        tool_name: str,
        args: Dict[str, Any],
        run_id: str
    ) -> ApprovalRequest:
        """Request approval for a tool call"""
        approval_request = ApprovalRequest(
            approval_id=f"approval_{uuid.uuid4().hex[:8]}",
            tool_name=tool_name,
            args=args,
            run_id=run_id,
            user_id=self.user_id,
            user_role=self.user_role,
            status="pending",
            created_at=datetime.utcnow()
        )
        
        self.approval_queue.add(approval_request)
        self._log_approval_request(approval_request)
        
        return approval_request
    
    def _execute_tool(
        self,
        tool_name: str,
        args: Dict[str, Any],
        run_id: str
    ) -> Dict[str, Any]:
        """Execute a tool (simulated)"""
        # Log tool call
        self._log_tool_call(run_id, tool_name, args)
        
        # Simulate tool execution
        if tool_name == "read_ticket":
            return {
                "status": "success",
                "result": {
                    "ticket": {
                        "id": args["ticket_id"],
                        "title": "Example ticket",
                        "status": "open",
                        "description": "This is an example ticket"
                    }
                }
            }
        elif tool_name == "add_comment":
            return {
                "status": "success",
                "result": {
                    "message": f"Comment added to ticket {args['ticket_id']}",
                    "comment_id": f"comment_{uuid.uuid4().hex[:8]}"
                }
            }
        elif tool_name == "close_ticket":
            return {
                "status": "success",
                "result": {
                    "message": f"Ticket {args['ticket_id']} closed",
                    "closed_at": datetime.utcnow().isoformat()
                }
            }
        else:
            return {
                "status": "error",
                "error": f"Tool {tool_name} execution not implemented"
            }
    
    def approve_action(self, approval_id: str, reviewer_id: str) -> Dict[str, Any]:
        """Approve an action and execute it"""
        approval = self.approval_queue.get(approval_id)
        
        if not approval:
            return {
                "status": "error",
                "error": "Approval not found"
            }
        
        if approval.status != "pending":
            return {
                "status": "error",
                "error": f"Approval already {approval.status}"
            }
        
        # Approve
        approval.status = "approved"
        approval.reviewer_id = reviewer_id
        approval.approved_at = datetime.utcnow()
        
        # Execute the tool
        result = self._execute_tool(
            approval.tool_name,
            approval.args,
            approval.run_id
        )
        
        # Log approval
        self._log_approval(approval)
        
        return result
    
    def reject_action(self, approval_id: str, reviewer_id: str, reason: str) -> Dict[str, Any]:
        """Reject an action"""
        approval = self.approval_queue.get(approval_id)
        
        if not approval:
            return {
                "status": "error",
                "error": "Approval not found"
            }
        
        if approval.status != "pending":
            return {
                "status": "error",
                "error": f"Approval already {approval.status}"
            }
        
        approval.status = "rejected"
        approval.reviewer_id = reviewer_id
        approval.rejected_at = datetime.utcnow()
        approval.rejection_reason = reason
        
        self._log_approval(approval)
        
        return {
            "status": "success",
            "message": "Action rejected"
        }
    
    def get_pending_approvals(self) -> List[ApprovalRequest]:
        """Get all pending approvals"""
        return self.approval_queue.get_pending()
    
    def _format_approval_summary(self, tool_name: str, args: Dict[str, Any]) -> str:
        """Format a summary of what the agent wants to do"""
        if tool_name == "close_ticket":
            return f"Close ticket {args.get('ticket_id')} with reason: {args.get('reason', 'N/A')}"
        return f"Execute {tool_name} with parameters: {json.dumps(args)}"
    
    def _get_safer_alternatives(self, tool_name: str) -> List[str]:
        """Get safer alternatives to a tool"""
        alternatives = {
            "close_ticket": ["add_comment", "read_ticket"],
            "delete_ticket": ["read_ticket"]
        }
        return alternatives.get(tool_name, ["read_ticket"])
    
    def _log_tool_call(self, run_id: str, tool_name: str, args: Dict[str, Any]):
        """Log a tool call"""
        log_entry = {
            "run_id": run_id,
            "timestamp": datetime.utcnow().isoformat(),
            "tool_name": tool_name,
            "args": self._redact_sensitive(args),
            "user_id": self.user_id,
            "user_role": self.user_role
        }
        
        self.tool_call_logs.append(log_entry)
        print(f"LOG: {json.dumps(log_entry)}")
    
    def _log_approval_request(self, approval: ApprovalRequest):
        """Log an approval request"""
        log_entry = {
            "approval_id": approval.approval_id,
            "timestamp": approval.created_at.isoformat(),
            "tool_name": approval.tool_name,
            "args": self._redact_sensitive(approval.args),
            "user_id": approval.user_id,
            "user_role": approval.user_role,
            "run_id": approval.run_id,
            "status": approval.status
        }
        print(f"APPROVAL_REQUEST: {json.dumps(log_entry)}")
    
    def _log_approval(self, approval: ApprovalRequest):
        """Log an approval decision"""
        log_entry = {
            "approval_id": approval.approval_id,
            "timestamp": datetime.utcnow().isoformat(),
            "tool_name": approval.tool_name,
            "status": approval.status,
            "reviewer_id": approval.reviewer_id,
            "approved_at": approval.approved_at.isoformat() if approval.approved_at else None,
            "rejected_at": approval.rejected_at.isoformat() if approval.rejected_at else None,
            "rejection_reason": getattr(approval, 'rejection_reason', None)
        }
        print(f"APPROVAL_DECISION: {json.dumps(log_entry)}")
    
    def _redact_sensitive(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Redact sensitive data from logs"""
        sensitive_keys = ["password", "api_key", "token", "secret", "ssn", "credit_card"]
        redacted = {}
        
        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                redacted[key] = "[REDACTED]"
            elif isinstance(value, dict):
                redacted[key] = self._redact_sensitive(value)
            else:
                redacted[key] = value
        
        return redacted
    
    def get_tool_call_logs(self, run_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get tool call logs, optionally filtered by run_id"""
        if run_id:
            return [log for log in self.tool_call_logs if log["run_id"] == run_id]
        return self.tool_call_logs

