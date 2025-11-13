"""Tests for Pydantic schemas."""

import pytest
from pydantic import ValidationError
from src.schemas import (
    TicketRouter,
    RouterOutput,
    EntityExtraction,
    StructuredSummary,
    ExtractionResult,
    TicketClassification
)


def test_ticket_router_valid():
    """Test valid TicketRouter."""
    router = TicketRouter(
        route="billing",
        priority="high",
        requires_escalation=True,
        tags=["payment", "refund"]
    )
    
    assert router.route == "billing"
    assert router.priority == "high"
    assert router.requires_escalation is True
    assert "payment" in router.tags


def test_ticket_router_invalid_route():
    """Test TicketRouter with invalid route."""
    with pytest.raises(ValidationError):
        TicketRouter(
            route="invalid_route",
            priority="high",
            requires_escalation=True
        )


def test_ticket_router_nullable_field():
    """Test TicketRouter with nullable estimated_resolution_time."""
    router = TicketRouter(
        route="tech_support",
        priority="medium",
        requires_escalation=False,
        estimated_resolution_time=None
    )
    
    assert router.estimated_resolution_time is None


def test_router_output_valid():
    """Test valid RouterOutput."""
    output = RouterOutput(
        route="billing",
        confidence=0.95,
        reasoning="User mentioned payment issue"
    )
    
    assert output.route == "billing"
    assert output.confidence == 0.95
    assert output.reasoning == "User mentioned payment issue"


def test_router_output_invalid_confidence():
    """Test RouterOutput with invalid confidence."""
    with pytest.raises(ValidationError):
        RouterOutput(
            route="billing",
            confidence=1.5,  # Should be <= 1.0
            reasoning="Test"
        )


def test_extraction_result_with_nulls():
    """Test ExtractionResult with null fields."""
    result = ExtractionResult(
        name=None,
        email=None,
        confidence=0.0
    )
    
    assert result.name is None
    assert result.email is None
    assert result.confidence == 0.0


def test_ticket_classification_valid():
    """Test valid TicketClassification."""
    classification = TicketClassification(
        intent="billing",
        priority="urgent",
        tags=["payment", "refund"]
    )
    
    assert classification.intent == "billing"
    assert classification.priority == "urgent"
    assert len(classification.tags) == 2

