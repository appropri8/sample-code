"""Example of using the support agent"""

from src.support_agent import SupportAgent


def main():
    """Example of using the support agent"""
    
    # Create agent as support agent
    agent = SupportAgent(user_role="support_agent", user_id="agent_001")
    
    print("=== Available tools ===")
    tools = agent.get_available_tools()
    print(f"Tools: {', '.join(tools)}\n")
    
    print("=== Example 1: Read ticket ===")
    result = agent.handle_user_request("read ticket TKT-12345")
    print(f"Result: {result}\n")
    
    print("=== Example 2: Add comment ===")
    result = agent.handle_user_request("add comment to TKT-12345: Customer issue resolved")
    print(f"Result: {result}\n")
    
    print("=== Example 3: Try to close ticket (will fail for support_agent) ===")
    result = agent.handle_user_request("close ticket TKT-12345")
    print(f"Result: {result}\n")
    
    # Create agent as manager
    print("=== Example 4: Manager trying to close ticket ===")
    manager = SupportAgent(user_role="support_manager", user_id="manager_001")
    result = manager.handle_user_request("close ticket TKT-12345 reason: Resolved")
    print(f"Result: {result}\n")
    
    if result.get("status") == "approval_required":
        approval_id = result.get("approval_id")
        print(f"=== Pending approvals ===")
        approvals = manager.get_pending_approvals()
        for approval in approvals:
            print(f"  Approval ID: {approval['approval_id']}")
            print(f"  Tool: {approval['tool_name']}")
            print(f"  Args: {approval['args']}")
            print()
        
        print(f"=== Approving {approval_id} ===")
        approval_result = manager.approve_action(
            approval_id=approval_id,
            reviewer_id="reviewer_001"
        )
        print(f"Approval result: {approval_result}\n")


if __name__ == "__main__":
    main()

