"""Example: Governance with safety toggles and approvals"""
from src.agent import Agent, AgentRole
from src.workflow import Workflow, WorkflowNode
from src.governance.safety import SafetyToggles
from src.governance.approval import ApprovalWorkflow


def main():
    """Run governance example"""
    # Safety toggles
    safety = SafetyToggles()
    
    print("=== Safety Toggles ===")
    print(f"Environment: {safety.env}")
    print(f"Can write: {safety.can_write('support_agent')}")
    print(f"Can call search_kb: {safety.can_call_tool('support_agent', 'search_kb')}")
    print(f"Can call delete_user: {safety.can_call_tool('support_agent', 'delete_user')}")
    print(f"Max cost: ${safety.get_max_cost()}")
    print(f"Max latency: {safety.get_max_latency()}ms")
    
    # Approval workflow
    approval = ApprovalWorkflow()
    
    print("\n=== Approval Workflow ===")
    trace_id = "trace_123"
    
    # Check if action requires approval
    requires = approval.requires_approval("update_billing")
    print(f"update_billing requires approval: {requires}")
    
    if requires:
        # Request approval
        approval_id = approval.request_approval(
            trace_id=trace_id,
            agent_role="billing_agent",
            action="update_billing",
            plan={
                "user_id": "123",
                "new_plan": "premium",
                "cost": 29.99
            }
        )
        print(f"Approval requested: {approval_id}")
        
        # Check status
        status = approval.check_approval(approval_id)
        print(f"Approval status: {status}")
        
        # Approve (in real system, this would be done by human)
        approval.approve(approval_id, "admin@example.com")
        status = approval.check_approval(approval_id)
        print(f"After approval, status: {status}")
    
    # Get pending approvals
    pending = approval.get_pending_approvals()
    print(f"\nPending approvals: {len(pending)}")


if __name__ == "__main__":
    main()

