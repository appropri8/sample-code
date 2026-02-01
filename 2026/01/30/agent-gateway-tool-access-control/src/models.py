"""Signed tool-call envelope and response models."""

from typing import Any, Optional

from pydantic import BaseModel, Field


class ToolCallEnvelope(BaseModel):
    """Signed envelope from agent: agent_id, version, request_id, tool, arguments."""

    agent_id: str = Field(..., description="Agent identifier")
    agent_version: str = Field(..., description="Agent version for audit")
    request_id: str = Field(..., description="Unique request id for tracing")
    tool: str = Field(..., description="Tool name")
    arguments: dict = Field(default_factory=dict, description="Tool arguments")
    role: Optional[str] = Field(default=None, description="Agent role (or derived from agent_id)")


class ToolCallResponse(BaseModel):
    """Gateway response: success, result or error, audit_id."""

    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None
    audit_id: str
    status: Optional[str] = None  # e.g. "pending_approval"
    approval_id: Optional[str] = None


class ApprovalRequest(BaseModel):
    """Approval action: approval_id, approved (bool)."""

    approval_id: str
    approved: bool = True
