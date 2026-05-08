import hashlib
import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


@dataclass
class Approval:
    approval_id: str
    trace_id: str
    tool_name: str
    fingerprint: str
    approver_role: str
    status: str
    approver: Optional[str] = None
    reason: Optional[str] = None
    created_at: Optional[str] = None
    approved_at: Optional[str] = None


class ApprovalService:
    def __init__(self):
        self._items = {}

    def create(self, trace_id, tool_name, arguments, approver_role):
        approval_id = f"appr_{uuid.uuid4().hex[:10]}"
        approval = Approval(
            approval_id=approval_id,
            trace_id=trace_id,
            tool_name=tool_name,
            fingerprint=_fingerprint(tool_name, arguments),
            approver_role=approver_role,
            status="pending",
            created_at=_now(),
        )
        self._items[approval_id] = approval
        return approval

    def approve(self, approval_id, approver, reason):
        approval = self._items[approval_id]
        approval.status = "approved"
        approval.approver = approver
        approval.reason = reason
        approval.approved_at = _now()
        return approval

    def require_approved(self, approval_id, tool_name, arguments):
        if approval_id not in self._items:
            raise ValueError("unknown approval id")

        approval = self._items[approval_id]
        if approval.status != "approved":
            raise ValueError("approval is not approved")

        if approval.fingerprint != _fingerprint(tool_name, arguments):
            raise ValueError("approval does not match this tool payload")

        return approval


def _fingerprint(tool_name, arguments):
    payload = {"tool": tool_name, "arguments": arguments}
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _now():
    return datetime.now(timezone.utc).isoformat()
