"""
Agent Gateway: one outbound path for tool calls.
Policy, secrets, audit. Signed envelope, allowlist by role, rate limit, approval flow.
"""

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from src.models import ToolCallEnvelope, ToolCallResponse, ApprovalRequest
from src.gateway.registry import get_tool, validate_arguments
from src.gateway.policy import allow_tool, has_forbidden_fields, requires_approval
from src.gateway.rate_limit import check_rate_limit
from src.gateway.audit import log_audit, audit_id
from src.gateway.approval import create_pending, consume_pending
from src.gateway.executor import execute_tool


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    # cleanup if any


app = FastAPI(title="Agent Gateway", description="Policy, Secrets, Audit", lifespan=lifespan)


def _resolve_role(envelope: ToolCallEnvelope) -> str:
    """Resolve agent role (e.g. from agent_id or envelope.role)."""
    if envelope.role:
        return envelope.role
    # Example: derive from agent_id prefix
    if envelope.agent_id.startswith("read_only_"):
        return "read_only_agent"
    return "action_agent"


@app.post("/api/tools/call", response_model=ToolCallResponse)
async def tool_call(envelope: ToolCallEnvelope):
    """
    Single entry point for tool calls. Signed envelope: agent_id, version, request_id, tool, arguments.
    Gateway validates, checks policy, rate limit, optional approval, then executes and audits.
    """
    role = _resolve_role(envelope)
    aid = audit_id()

    # 1. Tool in registry (deny by default)
    if not get_tool(envelope.tool):
        log_audit(
            request_id=envelope.request_id,
            agent_id=envelope.agent_id,
            agent_version=envelope.agent_version,
            tool=envelope.tool,
            role=role,
            policy_decision="deny",
            outcome="tool_not_in_registry",
            inputs_redacted=envelope.arguments,
        )
        raise HTTPException(status_code=403, detail="Tool not in registry (deny by default)")

    # 2. Forbidden fields in arguments
    forbidden = has_forbidden_fields(envelope.arguments)
    if forbidden:
        log_audit(
            request_id=envelope.request_id,
            agent_id=envelope.agent_id,
            agent_version=envelope.agent_version,
            tool=envelope.tool,
            role=role,
            policy_decision="deny",
            outcome="forbidden_fields",
            inputs_redacted=envelope.arguments,
            error_message=f"Forbidden fields: {forbidden}",
        )
        raise HTTPException(status_code=400, detail=f"Forbidden fields in request: {forbidden}")

    # 3. Schema validation
    valid, err = validate_arguments(envelope.tool, envelope.arguments)
    if not valid:
        log_audit(
            request_id=envelope.request_id,
            agent_id=envelope.agent_id,
            agent_version=envelope.agent_version,
            tool=envelope.tool,
            role=role,
            policy_decision="deny",
            outcome="validation_error",
            inputs_redacted=envelope.arguments,
            error_message=err,
        )
        raise HTTPException(status_code=400, detail=err or "Validation failed")

    # 4. Role allowlist
    if not allow_tool(role, envelope.tool):
        log_audit(
            request_id=envelope.request_id,
            agent_id=envelope.agent_id,
            agent_version=envelope.agent_version,
            tool=envelope.tool,
            role=role,
            policy_decision="deny",
            outcome="role_not_allowed",
            inputs_redacted=envelope.arguments,
        )
        raise HTTPException(status_code=403, detail=f"Role '{role}' not allowed for tool '{envelope.tool}'")

    # 5. Rate limit
    allowed, rate_err = check_rate_limit(envelope.agent_id, envelope.request_id)
    if not allowed:
        log_audit(
            request_id=envelope.request_id,
            agent_id=envelope.agent_id,
            agent_version=envelope.agent_version,
            tool=envelope.tool,
            role=role,
            policy_decision="deny",
            outcome="rate_limit_exceeded",
            inputs_redacted=envelope.arguments,
            error_message=rate_err,
        )
        raise HTTPException(status_code=429, detail=rate_err or "Rate limit exceeded")

    # 6. Approval required?
    if requires_approval(envelope.tool):
        approval_id = create_pending(
            envelope=envelope.model_dump(),
            tool=envelope.tool,
            arguments=envelope.arguments,
        )
        log_audit(
            request_id=envelope.request_id,
            agent_id=envelope.agent_id,
            agent_version=envelope.agent_version,
            tool=envelope.tool,
            role=role,
            policy_decision="pending_approval",
            outcome="pending_approval",
            inputs_redacted=envelope.arguments,
            approval_id=approval_id,
        )
        return ToolCallResponse(
            success=False,
            audit_id=aid,
            status="pending_approval",
            approval_id=approval_id,
            error="Human approval required",
        )

    # 7. Execute (mock: no secrets in this sample; in prod inject here)
    start = time.perf_counter()
    try:
        result = execute_tool(envelope.tool, envelope.arguments, _secrets=None)
        duration_ms = (time.perf_counter() - start) * 1000
        log_audit(
            request_id=envelope.request_id,
            agent_id=envelope.agent_id,
            agent_version=envelope.agent_version,
            tool=envelope.tool,
            role=role,
            policy_decision="allow",
            outcome="success",
            inputs_redacted=envelope.arguments,
            duration_ms=round(duration_ms, 2),
        )
        return ToolCallResponse(success=True, result=result, audit_id=aid)
    except Exception as e:
        duration_ms = (time.perf_counter() - start) * 1000
        log_audit(
            request_id=envelope.request_id,
            agent_id=envelope.agent_id,
            agent_version=envelope.agent_version,
            tool=envelope.tool,
            role=role,
            policy_decision="allow",
            outcome="error",
            inputs_redacted=envelope.arguments,
            error_message=str(e),
            duration_ms=round(duration_ms, 2),
        )
        return ToolCallResponse(success=False, error=str(e), audit_id=aid)


@app.post("/approve", response_model=ToolCallResponse)
async def approve(req: ApprovalRequest):
    """
    Human (or system) approves a pending tool call. Gateway executes and returns result.
    """
    pending = consume_pending(req.approval_id)
    if not pending:
        raise HTTPException(status_code=404, detail="Approval id not found or already consumed")

    if not req.approved:
        log_audit(
            request_id=pending["envelope"].get("request_id", ""),
            agent_id=pending["envelope"].get("agent_id", ""),
            agent_version=pending["envelope"].get("agent_version", ""),
            tool=pending["tool"],
            role=_resolve_role(ToolCallEnvelope(**pending["envelope"])),
            policy_decision="deny",
            outcome="approval_rejected",
            inputs_redacted=pending["arguments"],
        )
        return ToolCallResponse(
            success=False,
            audit_id=audit_id(),
            error="Approval rejected",
        )

    envelope = ToolCallEnvelope(**pending["envelope"])
    role = _resolve_role(envelope)
    aid = audit_id()
    start = time.perf_counter()
    try:
        result = execute_tool(pending["tool"], pending["arguments"], _secrets=None)
        duration_ms = (time.perf_counter() - start) * 1000
        log_audit(
            request_id=envelope.request_id,
            agent_id=envelope.agent_id,
            agent_version=envelope.agent_version,
            tool=pending["tool"],
            role=role,
            policy_decision="allow",
            outcome="success",
            inputs_redacted=pending["arguments"],
            duration_ms=round(duration_ms, 2),
            approval_id=req.approval_id,
        )
        return ToolCallResponse(success=True, result=result, audit_id=aid)
    except Exception as e:
        duration_ms = (time.perf_counter() - start) * 1000
        log_audit(
            request_id=envelope.request_id,
            agent_id=envelope.agent_id,
            agent_version=envelope.agent_version,
            tool=pending["tool"],
            role=role,
            policy_decision="allow",
            outcome="error",
            inputs_redacted=pending["arguments"],
            error_message=str(e),
            duration_ms=round(duration_ms, 2),
            approval_id=req.approval_id,
        )
        return ToolCallResponse(success=False, error=str(e), audit_id=aid)


@app.get("/health")
async def health():
    return {"status": "ok"}
