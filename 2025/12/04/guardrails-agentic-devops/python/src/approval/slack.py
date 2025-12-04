"""
Slack approval integration for agent actions.
Allows agents to request human approval via Slack interactive messages.
"""

import requests
from typing import Dict, Any
import json


class SlackApproval:
    """Handle approval requests via Slack."""
    
    def __init__(self, webhook_url: str, channel: str):
        """
        Initialize Slack approval handler.
        
        Args:
            webhook_url: Slack webhook URL for posting messages
            channel: Slack channel to post approval requests to
        """
        self.webhook_url = webhook_url
        self.channel = channel
    
    def request_approval(
        self,
        trace_id: str,
        agent_name: str,
        action: Dict[str, Any],
        plan_summary: str,
        diff: str
    ) -> str:
        """
        Request approval via Slack. Returns approval_id.
        
        Args:
            trace_id: Unique trace ID for this action
            agent_name: Name of the agent requesting approval
            action: Action details (tool, parameters, context)
            plan_summary: Human-readable summary of what will happen
            diff: Diff showing the proposed change
        
        Returns:
            Approval ID that can be used to track the approval
        """
        approval_id = f"approval_{trace_id}"
        
        # Create interactive message with buttons
        message = {
            "channel": self.channel,
            "text": f"🤖 {agent_name} requests approval for action",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "Agent Action Approval Required"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Agent:* {agent_name}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Trace ID:* `{trace_id}`"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Tool:* `{action['tool']}`"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Environment:* {action['context']['environment']}"
                        }
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Plan Summary:*\n{plan_summary}"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Proposed Change:*\n```\n{diff}\n```"
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "✅ Approve"
                            },
                            "style": "primary",
                            "value": f"{approval_id}:approve",
                            "action_id": "approve_action"
                        },
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "❌ Reject"
                            },
                            "style": "danger",
                            "value": f"{approval_id}:reject",
                            "action_id": "reject_action"
                        }
                    ]
                }
            ]
        }
        
        try:
            response = requests.post(
                self.webhook_url,
                json=message,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            response.raise_for_status()
            
            return approval_id
        
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to send Slack approval request: {str(e)}")


# Example usage
if __name__ == "__main__":
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
    
    print(f"Approval requested: {approval_id}")
