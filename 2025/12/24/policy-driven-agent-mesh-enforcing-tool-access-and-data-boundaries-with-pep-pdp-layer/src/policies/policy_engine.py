"""Simple policy engine for evaluating policies.

In production, use OPA (Open Policy Agent) or Cedar.
This is a simplified implementation for demonstration.
"""
from typing import Dict, Any, List


class PolicyEngine:
    """Simple policy engine."""
    
    def __init__(self):
        """Initialize policy engine."""
        self.policies = []
        self._load_default_policies()
    
    def _load_default_policies(self):
        """Load default policies."""
        # Policy 1: Allow ReadOrders if tenant matches and user has support_role
        self.policies.append({
            "id": "policy-read-orders-support",
            "condition": lambda ctx: (
                ctx["action"]["tool_name"] == "ReadOrders" and
                ctx["action"]["operation"] == "read" and
                ctx["subject"]["tenant_id"] == ctx["resource"].get("tenant_id") and
                "support_role" in ctx["subject"]["roles"]
            ),
            "decision": "allow",
            "constraints": {
                "field_masking": ["email"]
            },
            "reason": "User has support_role, tool is ReadOrders, tenant matches"
        })
        
        # Policy 2: Allow ReadOrders if tenant matches and user has admin_role
        self.policies.append({
            "id": "policy-read-orders-admin",
            "condition": lambda ctx: (
                ctx["action"]["tool_name"] == "ReadOrders" and
                ctx["action"]["operation"] == "read" and
                ctx["subject"]["tenant_id"] == ctx["resource"].get("tenant_id") and
                "admin_role" in ctx["subject"]["roles"]
            ),
            "decision": "allow",
            "constraints": {},
            "reason": "User has admin_role, tool is ReadOrders, tenant matches"
        })
        
        # Policy 3: Allow IssueRefund if user has finance_role
        self.policies.append({
            "id": "policy-issue-refund-finance",
            "condition": lambda ctx: (
                ctx["action"]["tool_name"] == "IssueRefund" and
                ctx["action"]["operation"] == "write" and
                "finance_role" in ctx["subject"]["roles"]
            ),
            "decision": "allow",
            "constraints": {},
            "reason": "User has finance_role, tool is IssueRefund"
        })
        
        # Policy 4: Allow ExportCSV if user has admin_role
        self.policies.append({
            "id": "policy-export-csv-admin",
            "condition": lambda ctx: (
                ctx["action"]["tool_name"] == "ExportCSV" and
                ctx["action"]["operation"] == "read" and
                "admin_role" in ctx["subject"]["roles"]
            ),
            "decision": "allow",
            "constraints": {
                "row_limit": 1000
            },
            "reason": "User has admin_role, tool is ExportCSV"
        })
        
        # Policy 5: Deny cross-tenant access
        self.policies.append({
            "id": "policy-deny-cross-tenant",
            "condition": lambda ctx: (
                ctx["action"]["tool_name"] == "ReadOrders" and
                ctx["subject"]["tenant_id"] != ctx["resource"].get("tenant_id")
            ),
            "decision": "deny",
            "constraints": {},
            "reason": "Cross-tenant access denied"
        })
    
    def evaluate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate policies and return decision.
        
        Args:
            context: Policy context (subject, action, resource, context)
            
        Returns:
            Decision dictionary
        """
        # Check policies in order
        for policy in self.policies:
            if policy["condition"](context):
                return {
                    "decision": policy["decision"],
                    "constraints": policy.get("constraints", {}),
                    "reason": policy.get("reason", ""),
                    "policy_id": policy["id"]
                }
        
        # Default deny
        return {
            "decision": "deny",
            "constraints": {},
            "reason": "No matching policy found",
            "policy_id": None
        }
    
    def add_policy(self, policy: Dict[str, Any]):
        """Add a custom policy.
        
        Args:
            policy: Policy dictionary with id, condition, decision, constraints, reason
        """
        self.policies.append(policy)

