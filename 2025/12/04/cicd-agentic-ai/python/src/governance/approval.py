"""Human approval workflow for destructive operations"""
from typing import Dict, Any, Optional
from enum import Enum
from datetime import datetime
import uuid


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ApprovalWorkflow:
    """Manage approval workflows for agent actions"""
    
    def __init__(self):
        self.pending_approvals = {}
    
    def requires_approval(self, action: str) -> bool:
        """Check if action requires approval"""
        destructive_actions = [
            "delete_user",
            "update_billing",
            "escalate_critical",
            "terraform_apply"
        ]
        return action in destructive_actions
    
    def request_approval(
        self,
        trace_id: str,
        agent_role: str,
        action: str,
        plan: Dict[str, Any]
    ) -> str:
        """Request approval for action"""
        approval_id = f"approval_{trace_id}_{action}_{uuid.uuid4().hex[:8]}"
        
        self.pending_approvals[approval_id] = {
            "trace_id": trace_id,
            "agent_role": agent_role,
            "action": action,
            "plan": plan,
            "status": ApprovalStatus.PENDING,
            "requested_at": datetime.utcnow().isoformat()
        }
        
        # In real implementation, send notification to human
        print(f"Approval requested: {approval_id} for action {action}")
        
        return approval_id
    
    def check_approval(self, approval_id: str) -> ApprovalStatus:
        """Check approval status"""
        approval = self.pending_approvals.get(approval_id)
        if not approval:
            return ApprovalStatus.REJECTED
        
        return ApprovalStatus(approval["status"])
    
    def approve(self, approval_id: str, approver: str):
        """Approve action"""
        approval = self.pending_approvals.get(approval_id)
        if approval:
            approval["status"] = ApprovalStatus.APPROVED.value
            approval["approver"] = approver
            approval["approved_at"] = datetime.utcnow().isoformat()
    
    def reject(self, approval_id: str, reason: str):
        """Reject action"""
        approval = self.pending_approvals.get(approval_id)
        if approval:
            approval["status"] = ApprovalStatus.REJECTED.value
            approval["rejection_reason"] = reason
            approval["rejected_at"] = datetime.utcnow().isoformat()
    
    def get_pending_approvals(self) -> List[Dict[str, Any]]:
        """Get all pending approvals"""
        return [
            approval for approval in self.pending_approvals.values()
            if approval["status"] == ApprovalStatus.PENDING.value
        ]

