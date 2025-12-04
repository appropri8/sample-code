"""
Example: Using policy engine to authorize agent actions.
"""

from src.policy import PolicyClient, PolicyDecision
import json


def main():
    # Initialize policy client (pointing to OPA server)
    policy_client = PolicyClient("http://localhost:8181")
    
    # Example 1: Check if scaling is allowed
    print("Example 1: Checking if scaling is allowed")
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
        print("❌ Action denied - cannot proceed")
    elif decision == PolicyDecision.ESCALATE:
        print("⚠️  Action requires human approval")
    elif decision == PolicyDecision.ALLOW:
        print("✅ Action allowed - proceeding")
    
    print()
    
    # Example 2: Check tool permission
    print("Example 2: Checking tool permission")
    can_call = policy_client.check_tool_permission(
        agent_role="observer",
        tool="scale_deployment"
    )
    
    if can_call:
        print("✅ Observer agent can call scale_deployment")
    else:
        print("❌ Observer agent cannot call scale_deployment (expected - observer is read-only)")
    
    print()
    
    # Example 3: Off-hours scaling (should escalate)
    print("Example 3: Off-hours scaling (should escalate)")
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
            "time": "2025-12-04T22:00:00Z",  # 10 PM - off hours
            "agent_role": "operator",
            "trace_id": "def456"
        }
    )
    
    print(f"Decision: {decision}, Reason: {reason}")
    if decision == PolicyDecision.ESCALATE:
        print("⚠️  Off-hours scaling requires approval (expected)")


if __name__ == "__main__":
    main()
