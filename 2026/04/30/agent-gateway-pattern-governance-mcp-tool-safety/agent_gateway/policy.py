import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class PolicyDecision:
    status: str
    reason: str
    policy_version: str
    approver_role: Optional[str] = None


class PolicyEngine:
    def __init__(self, version, rules, fallback):
        self.version = version
        self.rules = rules
        self.fallback = fallback

    @classmethod
    def from_file(cls, path):
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(raw["version"], raw["rules"], raw["fallback"])

    def evaluate(self, tool, arguments, context):
        roles = set(context.get("roles", []))

        for rule in self.rules:
            if rule["tool"] != tool.name:
                continue
            if not _matches(rule.get("when"), arguments):
                continue

            allowed_roles = set(rule.get("allowedRoles", []))
            if allowed_roles and roles.isdisjoint(allowed_roles):
                return PolicyDecision(
                    status="deny",
                    reason=f"role must be one of {sorted(allowed_roles)}",
                    policy_version=self.version,
                )

            return PolicyDecision(
                status=rule["decision"],
                reason=f"matched rule for {tool.name}",
                policy_version=self.version,
                approver_role=rule.get("approverRole"),
            )

        fallback_decision = self.fallback.get(tool.risk_tier, "deny")
        if tool.approval_required and fallback_decision == "allow":
            fallback_decision = "approval_required"

        return PolicyDecision(
            status=fallback_decision,
            reason=f"fallback for {tool.risk_tier} risk",
            policy_version=self.version,
            approver_role="operations_approver" if fallback_decision == "approval_required" else None,
        )


def _matches(condition, arguments):
    if not condition:
        return True

    field = condition.get("field")
    value = arguments.get(field)

    if "gt" in condition and not value > condition["gt"]:
        return False
    if "gte" in condition and not value >= condition["gte"]:
        return False
    if "lt" in condition and not value < condition["lt"]:
        return False
    if "lte" in condition and not value <= condition["lte"]:
        return False
    if "equals" in condition and value != condition["equals"]:
        return False

    return True
