"""JSON Schema definitions for schema-first LLM applications."""

from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import Literal, Optional
from datetime import datetime


class CustomerExtraction(BaseModel):
    """Extract customer information from text."""
    
    name: str = Field(description="Customer's full name")
    email: EmailStr = Field(description="Email address, must be valid format")
    phone: Optional[str] = Field(None, description="Phone number if found")
    priority: Literal[1, 2, 3, 4, 5] = Field(
        description="Priority level: 1=lowest, 5=highest"
    )
    tags: list[str] = Field(
        default_factory=list,
        description="Relevant tags for categorization"
    )


class TicketClassification(BaseModel):
    """Classify a support ticket."""
    
    intent: Literal["billing", "technical", "feature_request", "other"] = Field(
        description="The primary intent of the ticket"
    )
    priority: Literal["low", "medium", "high", "urgent"] = Field(
        description="Priority level based on urgency and impact"
    )
    tags: list[str] = Field(
        description="Relevant tags for categorization",
        default_factory=list
    )
    requires_escalation: bool = Field(
        default=False,
        description="True if this ticket needs immediate human review"
    )


class OrderExtraction(BaseModel):
    """Extract order information from text."""
    
    order_id: str = Field(description="Order identifier")
    customer_id: str = Field(description="Customer identifier")
    total: float = Field(ge=0.0, description="Order total, must be non-negative")
    status: Literal["pending", "processing", "shipped", "delivered", "cancelled"] = Field(
        description="Current order status"
    )
    created_at: datetime = Field(description="Order creation timestamp")
    notes: Optional[str] = Field(None, description="Additional notes")


# Tool argument schemas
class GetUserInfoArgs(BaseModel):
    """Arguments for get_user_info tool."""
    
    user_id: str = Field(description="User identifier")
    
    @field_validator('user_id')
    @classmethod
    def validate_user_id(cls, v):
        """Validate user_id format."""
        if not v or len(v) < 1:
            raise ValueError("user_id must be non-empty")
        if not v.startswith("user_"):
            raise ValueError("user_id must start with 'user_'")
        return v


class UpdateTicketArgs(BaseModel):
    """Arguments for update_ticket tool."""
    
    ticket_id: str = Field(description="Ticket identifier")
    status: Literal["open", "in_progress", "resolved", "closed"] = Field(
        description="New ticket status"
    )
    
    @field_validator('ticket_id')
    @classmethod
    def validate_ticket_id(cls, v):
        """Validate ticket_id format."""
        if not v.startswith("TICKET-"):
            raise ValueError("ticket_id must start with 'TICKET-'")
        return v


class SendNotificationArgs(BaseModel):
    """Arguments for send_notification tool."""
    
    user_id: str = Field(description="User identifier")
    message: str = Field(description="Notification message")
    priority: Literal["low", "medium", "high"] = Field(
        default="medium",
        description="Notification priority"
    )
    
    @field_validator('message')
    @classmethod
    def validate_message(cls, v):
        """Validate message length."""
        if len(v) > 500:
            raise ValueError("message must be 500 characters or less")
        return v
