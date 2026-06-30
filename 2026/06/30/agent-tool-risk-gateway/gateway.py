#!/usr/bin/env python3
"""
Tool-Risk Gateway: A control plane that sits between AI agents and external tools.

This is the complete reference implementation for the article
"The Agent Tool-Risk Gateway: Designing Approval, Policy, and Capability Boundaries
Before Tool Execution" (June 30, 2026).

Usage:
    uvicorn gateway:app --reload --port 8000

Then in another terminal:
    python agent_simulator.py
"""

import time
import uuid
import hmac
import hashlib
import json
import logging
from enum import Enum
from typing import Dict, List, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# ─── Logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("tool-risk-gateway")

# ─── Configuration ─────────────────────────────────────────────────────────────

GATEWAY_SECRET_KEY = "change-me-in-production-use-env-var"
CAPABILITY_TOKEN_TTL_SECONDS = 120
APPROVAL_TIMEOUT_SECONDS = 300

# ─── Risk Classification ───────────────────────────────────────────────────────


class RiskClass(Enum):
    """Risk taxonomy for tool calls. Higher = more dangerous."""

    READ_INTERNAL = 1
    READ_EXTERNAL = 2
    STATE_CHANGE = 3
    DESTRUCTIVE = 4
    IRREVERSIBLE = 5
    FINANCIAL = 6
    CROSS_TENANT_ADMIN = 7


# ─── Tool Definition ──────────────────────────────────────────────────────────


class ToolDefinition(BaseModel):
    """Metadata and policy constraints for a single tool."""

    name: str
    description: str
    input_schema: Dict
    risk_class: RiskClass
    allowed_roles: List[str]
    requires_approval: bool = False
    requires_dual_approval: bool = False
    max_scope: Optional[Dict] = None
    token_ttl_seconds: int = CAPABILITY_TOKEN_TTL_SECONDS
    audit_required: bool = True
    dry_run_supported: bool = False
    sandbox_required: bool = False


# ─── Tool Registry ────────────────────────────────────────────────────────────

TOOL_REGISTRY: Dict[str, ToolDefinition] = {
    "crm.get_customer": ToolDefinition(
        name="crm.get_customer",
        description="Look up a customer by ID in the CRM",
        input_schema={
            "type": "object",
            "properties": {
                "customer_id": {"type": "string", "minLength": 1, "maxLength": 64},
            },
            "required": ["customer_id"],
            "additionalProperties": False,
        },
        risk_class=RiskClass.READ_INTERNAL,
        allowed_roles=["*"],
        requires_approval=False,
    ),
    "crm.update_customer_status": ToolDefinition(
        name="crm.update_customer_status",
        description="Update a customer's status in the CRM",
        input_schema={
            "type": "object",
            "properties": {
                "customer_id": {"type": "string", "minLength": 1, "maxLength": 64},
                "status": {
                    "type": "string",
                    "enum": ["active", "inactive", "lead", "churned"],
                },
            },
            "required": ["customer_id", "status"],
            "additionalProperties": False,
        },
        risk_class=RiskClass.STATE_CHANGE,
        allowed_roles=["account_manager", "admin"],
        requires_approval=True,
        token_ttl_seconds=120,
    ),
    "email.send": ToolDefinition(
        name="email.send",
        description="Send an email to a customer",
        input_schema={
            "type": "object",
            "properties": {
                "to": {"type": "string", "format": "email"},
                "subject": {"type": "string", "maxLength": 200},
                "body": {"type": "string", "maxLength": 10000},
            },
            "required": ["to", "subject", "body"],
            "additionalProperties": False,
        },
        risk_class=RiskClass.IRREVERSIBLE,
        allowed_roles=["marketing", "admin"],
        requires_approval=True,
        sandbox_required=True,
    ),
    "file.delete": ToolDefinition(
        name="file.delete",
        description="Delete a file from the filesystem",
        input_schema={
            "type": "object",
            "properties": {
                "path": {"type": "string", "maxLength": 512},
                "recursive": {"type": "boolean", "default": False},
            },
            "required": ["path"],
            "additionalProperties": False,
        },
        risk_class=RiskClass.DESTRUCTIVE,
        allowed_roles=["admin"],
        requires_approval=True,
        max_scope={"allowed_dirs": ["/tmp/agent_workspace", "/home/user/sandbox"]},
    ),
    "payment.charge": ToolDefinition(
        name="payment.charge",
        description="Charge a customer a specific amount",
        input_schema={
            "type": "object",
            "properties": {
                "customer_id": {"type": "string"},
                "amount_cents": {"type": "integer", "minimum": 1, "maximum": 5000000},
                "currency": {"type": "string", "enum": ["USD", "EUR", "GBP"]},
            },
            "required": ["customer_id", "amount_cents", "currency"],
            "additionalProperties": False,
        },
        risk_class=RiskClass.FINANCIAL,
        allowed_roles=["admin"],
        requires_approval=True,
        requires_dual_approval=True,
    ),
    "knowledge_base.search": ToolDefinition(
        name="knowledge_base.search",
        description="Search the internal knowledge base",
        input_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "maxLength": 500},
                "max_results": {"type": "integer", "default": 5, "maximum": 50},
            },
            "required": ["query"],
            "additionalProperties": False,
        },
        risk_class=RiskClass.READ_INTERNAL,
        allowed_roles=["*"],
        requires_approval=False,
    ),
}


# ─── Policy Engine ─────────────────────────────────────────────────────────────


class Decision(Enum):
    """Possible gateway decisions for a proposed tool call."""

    ALLOW = "allow"
    DENY = "deny"
    APPROVAL_REQUIRED = "approval_required"
    SANDBOX_REQUIRED = "sandbox_required"
    DRY_RUN = "dry_run"


class PolicyRequest(BaseModel):
    """Incoming request from an agent proposing a tool call."""

    agent_id: str
    agent_role: str
    tool_name: str
    arguments: Dict
    request_id: str = ""


class PolicyResult(BaseModel):
    """Result of evaluating policy against a proposed tool call."""

    decision: Decision
    reason: str = ""
    approval_id: Optional[str] = None
    transformed_args: Optional[Dict] = None


def evaluate_policy(request: PolicyRequest) -> PolicyResult:
    """
    Evaluate whether a proposed tool call should be allowed, denied,
    or require human approval.

    This is the core policy decision function. It checks:
      1. Tool exists in registry
      2. Agent role is allowed to call this tool
      3. Arguments conform to the tool's JSON schema
      4. Scope constraints (e.g., allowed directories)
      5. Approval requirements (single or dual)
      6. Sandbox requirements
    """
    tool_def = TOOL_REGISTRY.get(request.tool_name)

    # 1. Registry check
    if not tool_def:
        return PolicyResult(decision=Decision.DENY, reason="Tool not found in registry")

    # 2. Role check
    if "*" not in tool_def.allowed_roles and request.agent_role not in tool_def.allowed_roles:
        return PolicyResult(
            decision=Decision.DENY,
            reason=f"Role '{request.agent_role}' is not allowed to call '{request.tool_name}'",
        )

    # 3. Schema validation
    try:
        from jsonschema import validate as json_validate

        json_validate(instance=request.arguments, schema=tool_def.input_schema)
    except Exception as exc:
        return PolicyResult(
            decision=Decision.DENY,
            reason=f"Schema validation failed: {exc}",
        )

    # 4. Scope check
    if tool_def.max_scope:
        allowed_dirs = tool_def.max_scope.get("allowed_dirs", [])
        if "path" in request.arguments:
            file_path = request.arguments["path"]
            if not any(file_path.startswith(d) for d in allowed_dirs):
                return PolicyResult(
                    decision=Decision.DENY,
                    reason=f"Path '{file_path}' is outside allowed directories",
                )

    # 5. Approval checks (most restrictive first)
    if tool_def.requires_dual_approval:
        return PolicyResult(
            decision=Decision.APPROVAL_REQUIRED,
            reason="Dual human approval required for this action",
        )

    if tool_def.requires_approval:
        return PolicyResult(
            decision=Decision.APPROVAL_REQUIRED,
            reason="Human approval required for this action",
        )

    # 6. Sandbox check
    if tool_def.sandbox_required:
        return PolicyResult(decision=Decision.SANDBOX_REQUIRED)

    # All checks passed
    return PolicyResult(decision=Decision.ALLOW)


# ─── Capability Token System ──────────────────────────────────────────────────


class CapabilityToken(BaseModel):
    """A short-lived, narrowly scoped token for executing one tool call."""

    token_id: str
    agent_id: str
    tool_name: str
    resource_id: Optional[str] = None
    action: str = ""
    issued_at: float = 0.0
    expires_at: float = 0.0
    scope: Dict = {}
    signature: str = ""


class CapabilityTokenIssuer:
    """
    Mints and verifies HMAC-signed capability tokens.

    Each token is scoped to:
      - One agent
      - One tool
      - One resource (e.g., customer ID)
      - One time window (TTL)
    """

    def __init__(self, secret_key: str):
        self.secret_key = secret_key

    def mint_token(
        self,
        agent_id: str,
        tool_def: ToolDefinition,
        arguments: Dict,
        ttl_seconds: int = CAPABILITY_TOKEN_TTL_SECONDS,
    ) -> CapabilityToken:
        now = time.time()
        resource_id = arguments.get("customer_id") or arguments.get("file_id")

        token = CapabilityToken(
            token_id=uuid.uuid4().hex[:16],
            agent_id=agent_id,
            tool_name=tool_def.name,
            resource_id=resource_id,
            action=tool_def.name.split(".")[-1],
            issued_at=now,
            expires_at=now + ttl_seconds,
            scope=arguments.copy(),
        )

        # Sign the token payload
        payload = json.dumps(token.model_dump(exclude={"signature"}), sort_keys=True)
        token.signature = hmac.new(
            self.secret_key.encode(), payload.encode(), hashlib.sha256
        ).hexdigest()

        return token

    def verify_token(self, token: CapabilityToken) -> bool:
        """Verify the token signature and TTL."""
        if token.expires_at < time.time():
            logger.warning(f"Expired token: {token.token_id}")
            return False

        payload = json.dumps(token.model_dump(exclude={"signature"}), sort_keys=True)
        expected_sig = hmac.new(
            self.secret_key.encode(), payload.encode(), hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(token.signature, expected_sig)


issuer = CapabilityTokenIssuer(GATEWAY_SECRET_KEY)


# ─── Approval Engine ──────────────────────────────────────────────────────────


class ApprovalRequest(BaseModel):
    """A pending approval request waiting for human intervention."""

    approval_id: str
    agent_id: str
    agent_role: str
    tool_name: str
    arguments: Dict
    status: str = "pending"  # pending | approved | rejected | expired
    created_at: float = 0.0
    timeout_seconds: int = APPROVAL_TIMEOUT_SECONDS
    approved_by: Optional[str] = None
    escalated_to: Optional[str] = None


# In-memory store — replace with database in production
pending_approvals: Dict[str, ApprovalRequest] = {}

# Audit log — append-only list in memory; write to DB in production
audit_log: List[Dict] = []


def append_audit_entry(entry: Dict) -> None:
    """Write an immutable audit entry."""
    entry["timestamp"] = datetime.now().isoformat()
    audit_log.append(entry)
    logger.info(f"AUDIT: {json.dumps(entry, default=str)}")


# ─── Execution Adapter ────────────────────────────────────────────────────────


async def execute_tool(tool_name: str, args: Dict, token: CapabilityToken) -> Dict:
    """
    Execute a tool call with a verified capability token.

    In production, this dispatches to the actual tool adapter (CRM SDK,
    email API client, filesystem library, etc.). Here we simulate execution.
    """
    if not issuer.verify_token(token):
        return {"error": "Token verification failed — token expired or invalid"}

    # Simulate tool execution
    logger.info(
        f"Executing {tool_name} with args {args} "
        f"(token: {token.token_id}, agent: {token.agent_id})"
    )

    # In a real adapter, you would:
    # 1. Resolve secrets (never received from agent)
    # 2. Call the external API/SDK
    # 3. Handle errors and timeouts
    # 4. Return the result

    return {
        "tool": tool_name,
        "status": "success",
        "executed_at": datetime.now().isoformat(),
    }


# ─── FastAPI Application ──────────────────────────────────────────────────────

app = FastAPI(
    title="Tool-Risk Gateway",
    description="A control plane for safe agent tool execution",
    version="1.0.0",
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "tool_count": len(TOOL_REGISTRY),
        "pending_approvals": len(pending_approvals),
    }


@app.get("/tools")
async def list_tools():
    """List all registered tools with their risk class and policy info."""
    return {
        name: {
            "name": t.name,
            "description": t.description,
            "risk_class": t.risk_class.name,
            "allowed_roles": t.allowed_roles,
            "requires_approval": t.requires_approval,
            "requires_dual_approval": t.requires_dual_approval,
        }
        for name, t in TOOL_REGISTRY.items()
    }


@app.post("/agent/propose-tool-call")
async def propose_tool_call(request: PolicyRequest):
    """
    Step 1: Agent proposes a tool call.

    The gateway evaluates policy and returns one of:
      - executed (auto-approved)
      - pending_approval (human needed)
      - denied (policy violation)
      - sandbox_required (needs isolated execution)
    """
    if not request.request_id:
        request.request_id = f"req_{uuid.uuid4().hex[:12]}"

    logger.info(
        f"Proposal: agent={request.agent_id} role={request.agent_role} "
        f"tool={request.tool_name} rid={request.request_id}"
    )

    result = evaluate_policy(request)

    # Log policy decision
    append_audit_entry(
        {
            "event": "policy_evaluation",
            "request_id": request.request_id,
            "agent_id": request.agent_id,
            "agent_role": request.agent_role,
            "tool_name": request.tool_name,
            "arguments_redacted": _redact_sensitive_fields(request.arguments),
            "decision": result.decision.value,
            "reason": result.reason,
        }
    )

    if result.decision == Decision.DENY:
        return {"status": "denied", "reason": result.reason, "request_id": request.request_id}

    if result.decision == Decision.APPROVAL_REQUIRED:
        approval_id = f"appr_{uuid.uuid4().hex[:12]}"
        pending_approvals[approval_id] = ApprovalRequest(
            approval_id=approval_id,
            agent_id=request.agent_id,
            agent_role=request.agent_role,
            tool_name=request.tool_name,
            arguments=request.arguments,
            created_at=time.time(),
        )
        return {
            "status": "pending_approval",
            "approval_id": approval_id,
            "request_id": request.request_id,
            "message": "This action requires human approval",
        }

    if result.decision == Decision.SANDBOX_REQUIRED:
        return {
            "status": "sandbox_required",
            "request_id": request.request_id,
            "message": "This action requires execution in a sandbox",
        }

    if result.decision == Decision.ALLOW:
        token = issuer.mint_token(
            request.agent_id,
            TOOL_REGISTRY[request.tool_name],
            request.arguments,
        )
        exec_result = await execute_tool(request.tool_name, request.arguments, token)
        append_audit_entry(
            {
                "event": "tool_executed",
                "request_id": request.request_id,
                "agent_id": request.agent_id,
                "tool_name": request.tool_name,
                "token_id": token.token_id,
                "outcome": "success",
            }
        )
        return {
            "status": "executed",
            "result": exec_result,
            "request_id": request.request_id,
        }

    return {
        "status": "denied",
        "reason": f"Unexpected decision: {result.decision}",
        "request_id": request.request_id,
    }


@app.post("/approve")
async def approve_action(approval_id: str, approver: str, approve: bool = True):
    """
    Step 2: A human approves or rejects a pending tool call.

    The gateway then executes (or rejects) the tool and logs the outcome.
    """
    approval = pending_approvals.get(approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval request not found")

    if approval.status != "pending":
        raise HTTPException(status_code=400, detail=f"Approval already processed: {approval.status}")

    # Check timeout
    if time.time() - approval.created_at > approval.timeout_seconds:
        approval.status = "expired"
        append_audit_entry(
            {
                "event": "approval_expired",
                "approval_id": approval_id,
                "agent_id": approval.agent_id,
                "tool_name": approval.tool_name,
            }
        )
        return {"status": "expired", "message": "Approval request timed out"}

    if not approve:
        approval.status = "rejected"
        approval.approved_by = approver
        append_audit_entry(
            {
                "event": "approval_rejected",
                "approval_id": approval_id,
                "approved_by": approver,
                "agent_id": approval.agent_id,
                "tool_name": approval.tool_name,
            }
        )
        return {"status": "rejected", "message": "Action rejected by approver"}

    # Approved — execute the tool
    approval.status = "approved"
    approval.approved_by = approver

    token = issuer.mint_token(
        approval.agent_id,
        TOOL_REGISTRY[approval.tool_name],
        approval.arguments,
    )
    exec_result = await execute_tool(approval.tool_name, approval.arguments, token)

    append_audit_entry(
        {
            "event": "approval_granted_and_executed",
            "approval_id": approval_id,
            "approved_by": approver,
            "agent_id": approval.agent_id,
            "tool_name": approval.tool_name,
            "token_id": token.token_id,
            "outcome": "success",
        }
    )

    return {
        "status": "approved_and_executed",
        "result": exec_result,
        "approval_id": approval_id,
    }


@app.get("/approvals/pending")
async def list_pending_approvals():
    """List all pending approval requests (for dashboard/Slack bot)."""
    return {
        "pending": [
            {
                "approval_id": a.approval_id,
                "agent_id": a.agent_id,
                "agent_role": a.agent_role,
                "tool_name": a.tool_name,
                "arguments_redacted": _redact_sensitive_fields(a.arguments),
                "created_at": datetime.fromtimestamp(a.created_at).isoformat(),
                "timeout_at": datetime.fromtimestamp(
                    a.created_at + a.timeout_seconds
                ).isoformat(),
            }
            for a in pending_approvals.values()
            if a.status == "pending"
        ]
    }


@app.get("/audit-log")
async def get_audit_log(limit: int = 20):
    """Retrieve recent audit log entries."""
    return {"entries": audit_log[-limit:]}


@app.get("/metrics")
async def get_metrics():
    """Return gateway metrics for dashboards and alerting."""
    total = len(audit_log)
    auto_approved = sum(1 for e in audit_log if e.get("decision") == "allow")
    denied = sum(1 for e in audit_log if e.get("decision") == "deny")
    approval_pending = sum(1 for a in pending_approvals.values() if a.status == "pending")

    return {
        "total_proposed": total,
        "auto_approved": auto_approved,
        "denied": denied,
        "approval_pending": approval_pending,
        "tools_registered": len(TOOL_REGISTRY),
    }


# ─── Helpers ───────────────────────────────────────────────────────────────────


def _redact_sensitive_fields(args: Dict) -> Dict:
    """Redact sensitive fields from logs (PII, secrets, etc.)."""
    redacted = args.copy()
    sensitive_keys = {"email", "password", "api_key", "token", "ssn", "credit_card"}
    for key in redacted:
        if key.lower() in sensitive_keys:
            redacted[key] = "***REDACTED***"
        elif isinstance(redacted[key], str) and len(redacted[key]) > 50:
            redacted[key] = redacted[key][:20] + "..."
    return redacted


# ─── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
