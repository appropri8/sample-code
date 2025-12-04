"""
Policy client for authorizing agent actions.
This client communicates with a policy service (e.g., OPA) to check
if an action is allowed, denied, or should be escalated.
"""

import requests
from typing import Dict, Any, Optional
from enum import Enum
import json


class PolicyDecision(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    ESCALATE = "escalate"


class PolicyClient:
    """Client for interacting with policy service."""
    
    def __init__(self, policy_service_url: str):
        """
        Initialize policy client.
        
        Args:
            policy_service_url: URL of the policy service (e.g., OPA server)
        """
        self.url = policy_service_url
    
    def authorize(
        self,
        tool: str,
        parameters: Dict[str, Any],
        context: Dict[str, Any]
    ) -> tuple[PolicyDecision, Optional[str]]:
        """
        Authorize an action. Returns (decision, reason).
        
        Args:
            tool: Name of the tool to call
            parameters: Parameters for the tool
            context: Context including environment, time, agent info, etc.
        
        Returns:
            Tuple of (decision, reason) where decision is ALLOW, DENY, or ESCALATE
        """
        action = {
            "tool": tool,
            "parameters": parameters,
            "context": context
        }
        
        try:
            response = requests.post(
                f"{self.url}/v1/data/deployment/scaling/allow",
                json={"input": action},
                timeout=5
            )
            response.raise_for_status()
            
            result = response.json()
            
            # OPA returns {"result": true/false} for allow
            if result.get("result"):
                # Check if escalation is needed
                escalate_response = requests.post(
                    f"{self.url}/v1/data/deployment/scaling/escalate",
                    json={"input": action},
                    timeout=5
                )
                escalate_result = escalate_response.json()
                
                if escalate_result.get("result"):
                    return PolicyDecision.ESCALATE, "Action requires human approval"
                else:
                    return PolicyDecision.ALLOW, "Action allowed"
            else:
                return PolicyDecision.DENY, "Action denied by policy"
        
        except requests.exceptions.RequestException as e:
            # On error, default to deny for safety
            return PolicyDecision.DENY, f"Policy service error: {str(e)}"
    
    def check_tool_permission(
        self,
        agent_role: str,
        tool: str
    ) -> bool:
        """
        Check if agent role can call tool.
        
        Args:
            agent_role: Role of the agent (observer, operator, admin)
            tool: Name of the tool
        
        Returns:
            True if allowed, False otherwise
        """
        try:
            response = requests.post(
                f"{self.url}/v1/data/tool/permissions/check",
                json={
                    "input": {
                        "agent_role": agent_role,
                        "tool": tool
                    }
                },
                timeout=5
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get("result", False)
        
        except requests.exceptions.RequestException:
            # On error, default to deny
            return False


# Example usage
if __name__ == "__main__":
    policy_client = PolicyClient("http://localhost:8181")
    
    # Example: Check if scaling is allowed
    decision, reason = policy_client.authorize(
        tool="scale_deployment",
        parameters={
            "namespace": "production",
            "deployment": "api",
            "replicas": 10
        },
        context={
            "current_replicas": 5,
            "environment": "production",
            "time": "2025-12-04T14:23:00Z",
            "agent_role": "operator",
            "trace_id": "abc123"
        }
    )
    
    print(f"Decision: {decision}, Reason: {reason}")
    
    if decision == PolicyDecision.DENY:
        print("Action denied - cannot proceed")
    elif decision == PolicyDecision.ESCALATE:
        print("Action requires human approval")
    elif decision == PolicyDecision.ALLOW:
        print("Action allowed - proceeding")
