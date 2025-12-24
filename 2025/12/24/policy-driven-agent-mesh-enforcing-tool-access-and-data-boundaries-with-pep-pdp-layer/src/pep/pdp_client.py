"""PDP (Policy Decision Point) client.

Simple implementation that evaluates policies locally.
In production, this would connect to OPA, Cedar, or another policy engine.
"""
from typing import Dict, Any
from src.policies.policy_engine import PolicyEngine


class PDPClient:
    """Policy Decision Point client."""
    
    def __init__(self, policy_engine: PolicyEngine = None):
        """Initialize PDP client.
        
        Args:
            policy_engine: Policy engine instance (creates new if None)
        """
        if policy_engine is None:
            from src.policies.policy_engine import PolicyEngine
            self.policy_engine = PolicyEngine()
        else:
            self.policy_engine = policy_engine
    
    def evaluate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate policies and return decision.
        
        Args:
            context: Policy context (subject, action, resource, context)
            
        Returns:
            Decision dictionary with:
            - decision: "allow" or "deny"
            - constraints: Dictionary of constraints (if allowed)
            - reason: Reason for decision
            - policy_id: ID of matching policy
        """
        return self.policy_engine.evaluate(context)

