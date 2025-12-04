"""
Example: Requesting human approval for agent actions.
"""

from src.approval import SlackApproval, ITSMApproval
import time


def slack_example():
    """Example using Slack approval."""
    print("Slack Approval Example")
    print("=" * 50)
    
    slack_approval = SlackApproval(
        webhook_url="https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
        channel="#ops-alerts"
    )
    
    approval_id = slack_approval.request_approval(
        trace_id="abc123",
        agent_name="ops-agent-v3",
        action={
            "tool": "scale_deployment",
            "parameters": {
                "namespace": "production",
                "deployment": "api",
                "replicas": 10
            },
            "context": {
                "environment": "production",
                "current_replicas": 5
            }
        },
        plan_summary="Scale deployment 'api' in 'production' from 5 to 10 replicas due to high CPU usage.",
        diff="- replicas: 5\n+ replicas: 10"
    )
    
    print(f"✅ Approval requested: {approval_id}")
    print("Check Slack channel #ops-alerts for approval request")
    print()


def itsm_example():
    """Example using ITSM approval."""
    print("ITSM Approval Example")
    print("=" * 50)
    
    itsm_approval = ITSMApproval(
        itsm_api_url="https://itsm.example.com",
        api_key="your-api-key"
    )
    
    ticket_id = itsm_approval.create_change_request(
        trace_id="def456",
        agent_name="ops-agent-v3",
        action={
            "tool": "scale_deployment",
            "parameters": {
                "namespace": "production",
                "deployment": "api",
                "replicas": 10
            },
            "context": {
                "environment": "production"
            }
        },
        plan_summary="Scale deployment 'api' in 'production' from 5 to 10 replicas."
    )
    
    print(f"✅ Change request created: {ticket_id}")
    print("Waiting for approval...")
    
    # Wait for approval (with timeout)
    approved = itsm_approval.wait_for_approval(ticket_id, timeout_seconds=60)
    
    if approved:
        print("✅ Change request approved - proceeding")
    else:
        print("❌ Change request rejected or timed out")


def main():
    print("Human-in-the-Loop Approval Examples")
    print("=" * 50)
    print()
    
    # Uncomment to test (requires actual webhook/API credentials)
    # slack_example()
    # itsm_example()
    
    print("Note: These examples require actual Slack webhook URLs or ITSM API credentials.")
    print("Uncomment the function calls above and provide valid credentials to test.")


if __name__ == "__main__":
    main()
