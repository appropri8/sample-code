import uuid
from pathlib import Path

from .approvals import ApprovalService
from .audit import AuditStore
from .mcp_broker import McpBroker
from .policy import PolicyEngine, PolicyDecision
from .registry import ToolRegistry
from .schema import ValidationError, validate_json


class AgentGateway:
    def __init__(self, registry, policy, approvals=None, broker=None, audit=None):
        self.registry = registry
        self.policy = policy
        self.approvals = approvals or ApprovalService()
        self.broker = broker or McpBroker()
        self.audit = audit or AuditStore()

    @classmethod
    def from_config(cls, root):
        root = Path(root)
        registry = ToolRegistry.from_file(root / "config" / "tool_registry.json")
        policy = PolicyEngine.from_file(root / "config" / "policies.json")
        return cls(registry=registry, policy=policy)

    def invoke(self, request):
        trace_id = request.get("traceId") or f"tr_{uuid.uuid4().hex[:10]}"
        agent_id = request.get("agentId", "unknown-agent")
        tool_name = request.get("toolName")
        arguments = request.get("arguments", {})
        context = request.get("context", {})

        try:
            tool = self.registry.get(tool_name)
        except KeyError as exc:
            return self._deny(trace_id, agent_id, tool_name, "unknown", str(exc), None)

        try:
            validate_json(tool.input_schema, arguments)
        except ValidationError as exc:
            return self._deny(trace_id, agent_id, tool.name, tool.risk_tier, str(exc), None)

        scopes = set(context.get("scopes", []))
        if tool.auth_scope not in scopes:
            return self._deny(
                trace_id,
                agent_id,
                tool.name,
                tool.risk_tier,
                f"missing scope: {tool.auth_scope}",
                None,
            )

        decision = self.policy.evaluate(tool, arguments, context)
        if decision.status == "deny":
            return self._deny(trace_id, agent_id, tool.name, tool.risk_tier, decision.reason, decision)

        approval = None
        if decision.status == "approval_required":
            approval_id = request.get("approvalId")
            if not approval_id:
                approval = self.approvals.create(
                    trace_id=trace_id,
                    tool_name=tool.name,
                    arguments=arguments,
                    approver_role=decision.approver_role or "operations_approver",
                )
                self.audit.log(
                    traceId=trace_id,
                    agentId=agent_id,
                    toolName=tool.name,
                    riskTier=tool.risk_tier,
                    decision="approval_required",
                    policyVersion=decision.policy_version,
                    approvalId=approval.approval_id,
                    approverRole=approval.approver_role,
                )
                return {
                    "status": "pending_approval",
                    "traceId": trace_id,
                    "approvalId": approval.approval_id,
                    "approverRole": approval.approver_role,
                }

            try:
                approval = self.approvals.require_approved(approval_id, tool.name, arguments)
            except ValueError as exc:
                return self._deny(trace_id, agent_id, tool.name, tool.risk_tier, str(exc), decision)

            decision = PolicyDecision(
                status="allow",
                reason="approved by human",
                policy_version=decision.policy_version,
                approver_role=approval.approver_role,
            )

        result = self.broker.call(
            server=tool.mcp_server,
            tool=tool.mcp_tool,
            arguments=arguments,
            trace_id=trace_id,
        )
        validate_json(tool.output_schema, result)

        self.audit.log(
            traceId=trace_id,
            agentId=agent_id,
            toolName=tool.name,
            riskTier=tool.risk_tier,
            decision="allow",
            policyVersion=decision.policy_version,
            approver=approval.approver if approval else None,
            resultStatus="success",
        )

        return {
            "status": "success",
            "traceId": trace_id,
            "toolName": tool.name,
            "data": result,
        }

    def approve(self, approval_id, approver, reason):
        return self.approvals.approve(approval_id, approver, reason)

    def _deny(self, trace_id, agent_id, tool_name, risk_tier, reason, decision):
        self.audit.log(
            traceId=trace_id,
            agentId=agent_id,
            toolName=tool_name,
            riskTier=risk_tier,
            decision="deny",
            policyVersion=decision.policy_version if decision else None,
            reason=reason,
        )
        return {
            "status": "denied",
            "traceId": trace_id,
            "toolName": tool_name,
            "reason": reason,
        }

