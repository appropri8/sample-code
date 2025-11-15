"""Approval system for high-risk tool calls"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime


@dataclass
class ApprovalRequest:
    """Represents an approval request"""
    approval_id: str
    tool_name: str
    args: Dict[str, Any]
    run_id: str
    user_id: str
    user_role: str
    status: str  # pending, approved, rejected
    created_at: datetime
    reviewer_id: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejected_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "approval_id": self.approval_id,
            "tool_name": self.tool_name,
            "args": self.args,
            "run_id": self.run_id,
            "user_id": self.user_id,
            "user_role": self.user_role,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "reviewer_id": self.reviewer_id,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "rejected_at": self.rejected_at.isoformat() if self.rejected_at else None,
            "rejection_reason": self.rejection_reason
        }


class ApprovalQueue:
    """Manages approval requests"""
    
    def __init__(self):
        self.requests: Dict[str, ApprovalRequest] = {}
    
    def add(self, approval: ApprovalRequest):
        """Add an approval request"""
        self.requests[approval.approval_id] = approval
    
    def get(self, approval_id: str) -> Optional[ApprovalRequest]:
        """Get an approval request by ID"""
        return self.requests.get(approval_id)
    
    def get_pending(self) -> List[ApprovalRequest]:
        """Get all pending approval requests"""
        return [
            approval for approval in self.requests.values()
            if approval.status == "pending"
        ]
    
    def get_all(self) -> List[ApprovalRequest]:
        """Get all approval requests"""
        return list(self.requests.values())
    
    def get_by_run_id(self, run_id: str) -> List[ApprovalRequest]:
        """Get approval requests for a specific run"""
        return [
            approval for approval in self.requests.values()
            if approval.run_id == run_id
        ]

