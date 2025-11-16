"""Tests for human handoff."""

import pytest
import asyncio
from src.human_handoff import (
    HumanHandoff,
    HandoffContext,
    ApprovalGateway,
    EscalationManager
)


class TestApprovalGateway:
    """Test approval gateway."""
    
    @pytest.mark.asyncio
    async def test_requires_approval(self):
        """Test that certain actions require approval."""
        gateway = ApprovalGateway()
        
        action = {"type": "payment", "amount": 100.0}
        result = await gateway.check_approval(action)
        
        assert result["requires_approval"] is True
        assert "approval_id" in result
    
    @pytest.mark.asyncio
    async def test_no_approval_needed(self):
        """Test that some actions don't need approval."""
        gateway = ApprovalGateway()
        
        action = {"type": "search", "query": "test"}
        result = await gateway.check_approval(action)
        
        assert result["requires_approval"] is False


class TestEscalationManager:
    """Test escalation manager."""
    
    @pytest.mark.asyncio
    async def test_escalation_after_threshold(self):
        """Test that escalation happens after threshold."""
        manager = EscalationManager(max_retries=3)
        error = Exception("Test error")
        context = {"operation": "test"}
        
        # Trigger escalation
        for i in range(3):
            await manager.handle_error(error, context)
        
        # Should have created ticket
        assert len(manager.tickets) > 0


class TestHumanHandoff:
    """Test human handoff."""
    
    @pytest.mark.asyncio
    async def test_ask_before_act(self):
        """Test ask-before-act pattern."""
        handoff = HumanHandoff()
        
        action = {"type": "payment", "amount": 100.0}
        context = HandoffContext(
            user_input="Process payment",
            plan={},
            executed_steps=[],
            failing_step=None,
            error=None
        )
        
        result = await handoff.ask_before_act(action, context)
        assert "status" in result
    
    @pytest.mark.asyncio
    async def test_stop_and_escalate(self):
        """Test stop-and-escalate pattern."""
        handoff = HumanHandoff()
        
        error = Exception("Critical error")
        context = HandoffContext(
            user_input="Test",
            plan={},
            executed_steps=[],
            failing_step=None,
            error=error
        )
        
        result = await handoff.stop_and_escalate(error, context)
        assert result["status"] == "escalated"
        assert "ticket_id" in result

