"""Example of human handoff patterns."""

import asyncio
import logging
from src.human_handoff import (
    HumanHandoff,
    HandoffContext,
    ApprovalGateway,
    EscalationManager
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Run human handoff examples."""
    handoff = HumanHandoff()
    
    print("=== Example 1: Approval Gateway ===\n")
    
    # Action that requires approval
    action = {
        "type": "payment",
        "amount": 100.0,
        "currency": "USD"
    }
    
    context = HandoffContext(
        user_input="Process payment",
        plan={"operation": "payment"},
        executed_steps=[],
        failing_step=None,
        error=None
    )
    
    result = await handoff.ask_before_act(action, context)
    print(f"Approval result: {result}\n")
    
    # Action that doesn't require approval
    action2 = {
        "type": "search",
        "query": "test"
    }
    
    result2 = await handoff.ask_before_act(action2, context)
    print(f"No approval needed: {result2}\n")
    
    print("=== Example 2: Escalation Manager ===\n")
    
    # Simulate repeated errors
    error = Exception("Test error")
    escalation_context = {
        "operation": "test_operation",
        "user_input": "Test input"
    }
    
    print("Simulating 3 errors to trigger escalation...")
    for i in range(3):
        await handoff.escalation_manager.handle_error(error, escalation_context)
        print(f"Error {i+1} handled")
    
    print("\n=== Example 3: Stop and Escalate ===\n")
    
    # Stop and escalate
    error2 = Exception("Critical error")
    context2 = HandoffContext(
        user_input="Test operation",
        plan={"operation": "test"},
        executed_steps=[
            {"step": "step1", "result": "success"},
            {"step": "step2", "result": "success"}
        ],
        failing_step={"step": "step3", "error": "failed"},
        error=error2,
        agent_suggestion="Please review the error and provide guidance"
    )
    
    result3 = await handoff.stop_and_escalate(error2, context2)
    print(f"Escalation result: {result3}\n")
    
    print("=== Example 4: Context Packaging ===\n")
    
    from src.human_handoff import package_context_for_human
    
    context3 = package_context_for_human(
        user_input="User wants to update record",
        plan={"steps": ["step1", "step2", "step3"]},
        executed_steps=[
            {"step": "step1", "result": "success"},
            {"step": "step2", "result": "success"}
        ],
        failing_step={"step": "step3", "params": {"id": "123"}},
        error=Exception("Update failed"),
        agent_suggestion="Record might be locked, please check permissions"
    )
    
    print("Packaged context:")
    print(context3.to_dict())


if __name__ == "__main__":
    asyncio.run(main())

