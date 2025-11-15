"""Basic usage example of the policy layer"""

from src.policy_layer import PolicyLayer
from src.tool_registry import get_tools_for_role


def main():
    """Basic example of using the policy layer"""
    
    # Create policy layer for a support agent
    policy = PolicyLayer(user_role="support_agent", user_id="user_123")
    
    print("=== Example 1: Allowed tool call ===")
    result = policy.call_tool_with_policy(
        tool_name="read_ticket",
        args={"ticket_id": "TKT-12345"},
        run_id="run_001"
    )
    print(f"Result: {result}\n")
    
    print("=== Example 2: Permission denied ===")
    result = policy.call_tool_with_policy(
        tool_name="close_ticket",
        args={"ticket_id": "TKT-12345", "reason": "Resolved"},
        run_id="run_002"
    )
    print(f"Result: {result}\n")
    
    print("=== Example 3: Validation error ===")
    result = policy.call_tool_with_policy(
        tool_name="add_comment",
        args={"ticket_id": "TKT-12345"},  # Missing 'comment' field
        run_id="run_003"
    )
    print(f"Result: {result}\n")
    
    print("=== Example 4: Approval required (as manager) ===")
    policy_manager = PolicyLayer(user_role="support_manager", user_id="manager_123")
    result = policy_manager.call_tool_with_policy(
        tool_name="close_ticket",
        args={"ticket_id": "TKT-12345", "reason": "Resolved by manager"},
        run_id="run_004"
    )
    print(f"Result: {result}\n")
    
    if result.get("status") == "approval_required":
        approval_id = result.get("approval_id")
        print(f"=== Approving action {approval_id} ===")
        approval_result = policy_manager.approve_action(
            approval_id=approval_id,
            reviewer_id="reviewer_001"
        )
        print(f"Approval result: {approval_result}\n")
    
    print("=== Available tools for support_agent ===")
    tools = get_tools_for_role("support_agent")
    for tool in tools:
        print(f"  - {tool.name}: {tool.description}")


if __name__ == "__main__":
    main()

