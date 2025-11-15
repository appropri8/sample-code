"""Simple CLI for managing approvals"""

import sys
from src.policy_layer import PolicyLayer
from src.support_agent import SupportAgent


def list_approvals(policy: PolicyLayer):
    """List all pending approvals"""
    approvals = policy.get_pending_approvals()
    
    if not approvals:
        print("No pending approvals")
        return
    
    print(f"\n=== Pending Approvals ({len(approvals)}) ===\n")
    
    for i, approval in enumerate(approvals, 1):
        print(f"{i}. Approval ID: {approval.approval_id}")
        print(f"   Tool: {approval.tool_name}")
        print(f"   User: {approval.user_id} ({approval.user_role})")
        print(f"   Run ID: {approval.run_id}")
        print(f"   Args: {approval.args}")
        print(f"   Created: {approval.created_at.isoformat()}")
        print()


def approve_action(policy: PolicyLayer, approval_id: str, reviewer_id: str = "cli_reviewer"):
    """Approve an action"""
    result = policy.approve_action(approval_id, reviewer_id)
    
    if result.get("status") == "success":
        print(f"✓ Approved and executed: {approval_id}")
        print(f"  Result: {result.get('result')}")
    else:
        print(f"✗ Failed to approve: {result.get('error')}")


def reject_action(policy: PolicyLayer, approval_id: str, reason: str, reviewer_id: str = "cli_reviewer"):
    """Reject an action"""
    result = policy.reject_action(approval_id, reviewer_id, reason)
    
    if result.get("status") == "success":
        print(f"✓ Rejected: {approval_id}")
        print(f"  Reason: {reason}")
    else:
        print(f"✗ Failed to reject: {result.get('error')}")


def main():
    """CLI main function"""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python approval_cli.py list")
        print("  python approval_cli.py approve <approval_id> [reviewer_id]")
        print("  python approval_cli.py reject <approval_id> <reason> [reviewer_id]")
        print("\nExample:")
        print("  python approval_cli.py list")
        print("  python approval_cli.py approve approval_abc123 reviewer_001")
        print("  python approval_cli.py reject approval_abc123 'Not appropriate' reviewer_001")
        sys.exit(1)
    
    # Create a policy layer (in real usage, this would be shared state)
    # For demo, we'll create a manager policy
    policy = PolicyLayer(user_role="support_manager", user_id="cli_user")
    
    command = sys.argv[1]
    
    if command == "list":
        list_approvals(policy)
    
    elif command == "approve":
        if len(sys.argv) < 3:
            print("Error: approval_id required")
            sys.exit(1)
        
        approval_id = sys.argv[2]
        reviewer_id = sys.argv[3] if len(sys.argv) > 3 else "cli_reviewer"
        approve_action(policy, approval_id, reviewer_id)
    
    elif command == "reject":
        if len(sys.argv) < 4:
            print("Error: approval_id and reason required")
            sys.exit(1)
        
        approval_id = sys.argv[2]
        reason = sys.argv[3]
        reviewer_id = sys.argv[4] if len(sys.argv) > 4 else "cli_reviewer"
        reject_action(policy, approval_id, reason, reviewer_id)
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()

