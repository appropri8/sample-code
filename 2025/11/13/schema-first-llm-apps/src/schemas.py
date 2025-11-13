"""Pydantic schemas for schema-first LLM applications."""

from pydantic import BaseModel, Field, validator
from typing import Literal, Optional, List
from datetime import datetime


class TicketRouter(BaseModel):
    """Routes support tickets to the appropriate team."""
    
    route: Literal["billing", "tech_support", "sales", "other"] = Field(
        description="Which team should handle this ticket"
    )
    priority: Literal["low", "medium", "high", "urgent"] = Field(
        description="Ticket priority based on urgency and business impact"
    )
    requires_escalation: bool = Field(
        description="True if this ticket needs immediate human review"
    )
    estimated_resolution_time: Optional[int] = Field(
        None,
        description="Estimated resolution time in minutes, or null if unknown"
    )
    tags: List[str] = Field(
        default_factory=list,
        description="Tags for categorization and filtering"
    )


class EntityExtraction(BaseModel):
    """Extract entities from text."""
    
    entities: List[dict] = Field(
        description="List of entities with type, value, and confidence"
    )
    dates: List[str] = Field(
        description="Extracted dates in ISO format"
    )
    decisions: List[str] = Field(
        description="Key decisions or action items mentioned"
    )


class RouterOutput(BaseModel):
    """Routes requests to appropriate handlers."""
    
    route: Literal["billing", "tech_support", "sales", "other"] = Field(
        description="Route to billing for payment/refund issues, tech_support for technical problems, sales for product questions, other for everything else"
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence in routing decision"
    )
    reasoning: str = Field(
        description="Brief explanation of routing decision"
    )


class StructuredSummary(BaseModel):
    """Structured summary of a document or conversation."""
    
    title: str = Field(description="Concise title summarizing the content")
    summary: str = Field(description="2-3 sentence summary of key points")
    risks: List[str] = Field(
        default_factory=list,
        description="List of identified risks or concerns"
    )
    next_actions: List[str] = Field(
        default_factory=list,
        description="Recommended next actions or follow-ups"
    )
    key_entities: List[str] = Field(
        default_factory=list,
        description="Important people, places, or concepts mentioned"
    )


class ExtractionResult(BaseModel):
    """Extraction result with optional fields."""
    
    name: Optional[str] = Field(None, description="Extracted name, or null if not found")
    email: Optional[str] = Field(None, description="Extracted email, or null if not found")
    confidence: float = Field(description="Confidence score 0.0-1.0")


class TicketClassification(BaseModel):
    """Classify a support ticket."""
    
    intent: Literal["billing", "technical", "feature_request", "other"] = Field(
        description="The primary intent of the ticket"
    )
    priority: Literal["low", "medium", "high", "urgent"] = Field(
        description="Priority level based on urgency and impact"
    )
    tags: List[str] = Field(
        description="Relevant tags for categorization",
        default_factory=list
    )

