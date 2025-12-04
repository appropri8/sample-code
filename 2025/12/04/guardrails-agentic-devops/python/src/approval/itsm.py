"""
ITSM (IT Service Management) approval integration.
Allows agents to create change requests in ITSM tools like ServiceNow, Jira, etc.
"""

import requests
from typing import Dict, Any, Optional
from datetime import datetime
import json


class ITSMApproval:
    """Handle approval requests via ITSM system."""
    
    def __init__(self, itsm_api_url: str, api_key: str):
        """
        Initialize ITSM approval handler.
        
        Args:
            itsm_api_url: Base URL of the ITSM API
            api_key: API key for authentication
        """
        self.url = itsm_api_url
        self.api_key = api_key
    
    def create_change_request(
        self,
        trace_id: str,
        agent_name: str,
        action: Dict[str, Any],
        plan_summary: str
    ) -> str:
        """
        Create change request in ITSM. Returns ticket_id.
        
        Args:
            trace_id: Unique trace ID for this action
            agent_name: Name of the agent requesting approval
            action: Action details (tool, parameters, context)
            plan_summary: Human-readable summary of what will happen
        
        Returns:
            Ticket ID from the ITSM system
        """
        change_request = {
            "title": f"Agent Action: {action['tool']}",
            "description": f"""
Agent: {agent_name}
Trace ID: {trace_id}
Tool: {action['tool']}
Environment: {action['context']['environment']}

Plan Summary:
{plan_summary}

Parameters:
{json.dumps(action['parameters'], indent=2)}
            """,
            "category": "automated",
            "priority": "medium",
            "requested_by": f"agent:{agent_name}",
            "approval_required": True,
            "created_at": datetime.utcnow().isoformat()
        }
        
        try:
            response = requests.post(
                f"{self.url}/api/change-requests",
                json=change_request,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                timeout=10
            )
            response.raise_for_status()
            
            ticket = response.json()
            return ticket["id"]
        
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to create ITSM change request: {str(e)}")
    
    def check_approval_status(self, ticket_id: str) -> str:
        """
        Check if ticket is approved. Returns 'approved', 'rejected', or 'pending'.
        
        Args:
            ticket_id: Ticket ID from the ITSM system
        
        Returns:
            Status: 'approved', 'rejected', or 'pending'
        """
        try:
            response = requests.get(
                f"{self.url}/api/change-requests/{ticket_id}",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=10
            )
            response.raise_for_status()
            
            ticket = response.json()
            return ticket["status"]  # 'approved', 'rejected', 'pending'
        
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to check ITSM ticket status: {str(e)}")
    
    def wait_for_approval(
        self,
        ticket_id: str,
        timeout_seconds: int = 3600,
        check_interval_seconds: int = 30
    ) -> bool:
        """
        Wait for ticket approval. Returns True if approved, False if rejected or timeout.
        
        Args:
            ticket_id: Ticket ID to wait for
            timeout_seconds: Maximum time to wait
            check_interval_seconds: How often to check status
        
        Returns:
            True if approved, False otherwise
        """
        import time
        start_time = time.time()
        
        while time.time() - start_time < timeout_seconds:
            status = self.check_approval_status(ticket_id)
            
            if status == "approved":
                return True
            elif status == "rejected":
                return False
            
            time.sleep(check_interval_seconds)
        
        # Timeout
        return False


# Example usage
if __name__ == "__main__":
    itsm_approval = ITSMApproval(
        itsm_api_url="https://itsm.example.com",
        api_key="your-api-key"
    )
    
    ticket_id = itsm_approval.create_change_request(
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
                "environment": "production"
            }
        },
        plan_summary="Scale deployment 'api' in 'production' from 5 to 10 replicas."
    )
    
    print(f"Change request created: {ticket_id}")
    
    # Wait for approval
    approved = itsm_approval.wait_for_approval(ticket_id)
    if approved:
        print("Change request approved - proceeding")
    else:
        print("Change request rejected or timed out")
