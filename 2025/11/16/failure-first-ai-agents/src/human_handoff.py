"""Human handoff and escalation patterns."""

import asyncio
import time
import uuid
import logging
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


class HandoffType(Enum):
    """Types of human handoffs."""
    ASK_BEFORE_ACT = "ask_before_act"
    REVIEW_AFTER_ACT = "review_after_act"
    STOP_AND_ESCALATE = "stop_and_escalate"


@dataclass
class HandoffContext:
    """Context for human handoff."""
    user_input: str
    plan: Dict[str, Any]
    executed_steps: List[Dict[str, Any]]
    failing_step: Optional[Dict[str, Any]]
    error: Optional[Exception]
    agent_suggestion: Optional[str] = None
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        result = asdict(self)
        if self.error:
            result["error"] = {
                "message": str(self.error),
                "type": type(self.error).__name__
            }
        return result


class ApprovalGateway:
    """Gateway for actions that require human approval."""
    
    def __init__(self):
        self.requires_approval = [
            "payment",
            "delete_user",
            "update_pii",
            "change_production_config",
            "external_api_call"
        ]
        self.pending_approvals = {}
    
    async def check_approval(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Check if action requires approval."""
        action_type = action.get("type")
        
        if action_type in self.requires_approval:
            # Create approval request
            approval_id = await self._create_approval_request(action)
            
            return {
                "requires_approval": True,
                "approval_id": approval_id,
                "action": action,
                "message": f"Action '{action_type}' requires approval"
            }
        
        return {
            "requires_approval": False,
            "action": action
        }
    
    async def _create_approval_request(self, action: Dict[str, Any]) -> str:
        """Create an approval request and notify human."""
        approval_id = str(uuid.uuid4())
        
        # Store request
        self.pending_approvals[approval_id] = {
            "action": action,
            "status": "pending",
            "created_at": time.time()
        }
        
        # Notify human (in production, send to Slack, email, etc.)
        logger.info(f"Approval requested: {approval_id} for action {action.get('type')}")
        
        return approval_id
    
    async def wait_for_approval(self, approval_id: str, timeout: float = 300.0) -> bool:
        """Wait for approval (simulated)."""
        # In production, poll approval system or use webhooks
        await asyncio.sleep(0.1)  # Simulate wait
        
        # For demo, auto-approve after timeout
        if approval_id in self.pending_approvals:
            return True
        return False


class EscalationManager:
    """Manage escalation when errors repeat."""
    
    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries
        self.error_counts = {}
        self.tickets = {}
    
    async def handle_error(self, error: Exception, context: Dict[str, Any]):
        """Handle error and escalate if needed."""
        error_key = self._error_key(error, context)
        
        # Increment count
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
        count = self.error_counts[error_key]
        
        logger.warning(f"Error occurred: {error} (count: {count})")
        
        # If threshold reached, escalate
        if count >= self.max_retries:
            await self._escalate(error, context, count)
    
    async def _escalate(self, error: Exception, context: Dict[str, Any], count: int):
        """Escalate to human."""
        logger.error(f"Escalating error after {count} occurrences: {error}")
        
        # Create ticket
        ticket_id = await self._create_ticket(error, context)
        
        # Send alert (in production, send to Slack, Teams, etc.)
        await self._send_alert(error, context, ticket_id)
    
    def _error_key(self, error: Exception, context: Dict[str, Any]) -> str:
        """Generate a key for grouping similar errors."""
        error_type = type(error).__name__
        operation = context.get("operation", "unknown")
        return f"{error_type}:{operation}"
    
    async def _create_ticket(self, error: Exception, context: Dict[str, Any]) -> str:
        """Create a support ticket."""
        ticket_id = f"TICKET-{int(time.time())}"
        
        self.tickets[ticket_id] = {
            "error": str(error),
            "error_type": type(error).__name__,
            "context": context,
            "created_at": time.time(),
            "status": "open"
        }
        
        logger.info(f"Ticket created: {ticket_id}")
        return ticket_id
    
    async def _send_alert(self, error: Exception, context: Dict[str, Any], ticket_id: str):
        """Send alert to human (simulated)."""
        logger.info(f"Alert sent for ticket {ticket_id}: {error}")


def package_context_for_human(
    user_input: str,
    plan: Dict[str, Any],
    executed_steps: List[Dict[str, Any]],
    failing_step: Optional[Dict[str, Any]],
    error: Optional[Exception],
    agent_suggestion: Optional[str] = None
) -> HandoffContext:
    """Package context for human review."""
    return HandoffContext(
        user_input=user_input,
        plan=plan,
        executed_steps=executed_steps,
        failing_step=failing_step,
        error=error,
        agent_suggestion=agent_suggestion or "Please review and provide guidance"
    )


class HumanHandoff:
    """Human handoff manager."""
    
    def __init__(self):
        self.approval_gateway = ApprovalGateway()
        self.escalation_manager = EscalationManager()
    
    async def ask_before_act(
        self,
        action: Dict[str, Any],
        context: HandoffContext
    ) -> Dict[str, Any]:
        """Ask human before acting."""
        # Check if approval needed
        approval_check = await self.approval_gateway.check_approval(action)
        
        if approval_check.get("requires_approval"):
            approval_id = approval_check["approval_id"]
            
            # Package context
            handoff_context = HandoffContext(
                user_input=context.user_input,
                plan={"proposed_action": action},
                executed_steps=[],
                failing_step=None,
                error=None,
                agent_suggestion=f"Proposed action: {action.get('type')}"
            )
            
            # Wait for approval
            approved = await self.approval_gateway.wait_for_approval(approval_id)
            
            if approved:
                return {
                    "status": "approved",
                    "action": action,
                    "approval_id": approval_id
                }
            else:
                return {
                    "status": "cancelled",
                    "reason": "Not approved",
                    "approval_id": approval_id
                }
        
        return {
            "status": "no_approval_needed",
            "action": action
        }
    
    async def stop_and_escalate(
        self,
        error: Exception,
        context: HandoffContext
    ) -> Dict[str, Any]:
        """Stop execution and escalate to human."""
        # Handle error
        await self.escalation_manager.handle_error(error, {
            "operation": context.plan.get("operation", "unknown"),
            "user_input": context.user_input
        })
        
        # Create ticket
        ticket_id = await self.escalation_manager._create_ticket(error, context.to_dict())
        
        return {
            "status": "escalated",
            "ticket_id": ticket_id,
            "context": context.to_dict(),
            "message": "Error escalated to human for review"
        }


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def main():
        handoff = HumanHandoff()
        
        # Test approval gateway
        action = {"type": "payment", "amount": 100.0, "currency": "USD"}
        result = await handoff.ask_before_act(action, HandoffContext(
            user_input="Process payment",
            plan={},
            executed_steps=[],
            failing_step=None,
            error=None
        ))
        print(f"Approval result: {result}")
        
        # Test escalation
        error = Exception("Test error")
        context = HandoffContext(
            user_input="Test operation",
            plan={"operation": "test"},
            executed_steps=[],
            failing_step=None,
            error=error
        )
        
        # Simulate multiple errors
        for i in range(3):
            await handoff.escalation_manager.handle_error(error, {"operation": "test"})
        
        escalation_result = await handoff.stop_and_escalate(error, context)
        print(f"Escalation result: {escalation_result}")
    
    asyncio.run(main())

