"""
Example 1: Pydantic Schema Definitions

Demonstrates comprehensive schema design with:
- Required and optional fields
- Enums and literals
- Field constraints
- Nested objects
- Schema versioning
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Literal
from datetime import datetime


# Simple schema with required fields
class TaskExtractionV1(BaseModel):
    """Extract task information from text - Version 1"""
    
    version: Literal["1.0"] = "1.0"
    title: str = Field(
        description="Task title",
        min_length=5,
        max_length=100
    )
    priority: Literal[1, 2, 3, 4, 5] = Field(
        description="Priority level: 1=lowest, 5=highest"
    )


# Enhanced schema with optional fields
class TaskExtractionV2(BaseModel):
    """Extract task information from text - Version 2"""
    
    version: Literal["2.0"] = "2.0"
    
    # Required fields
    title: str = Field(
        description="Task title",
        min_length=5,
        max_length=100
    )
    priority: Literal[1, 2, 3, 4, 5] = Field(
        description="Priority level: 1=lowest, 5=highest"
    )
    category: Literal["bug", "feature", "docs", "refactor"] = Field(
        description="Task category"
    )
    
    # Optional fields with defaults
    description: str | None = Field(
        None,
        description="Detailed task description",
        max_length=500
    )
    estimated_hours: float | None = Field(
        None,
        description="Estimated hours to complete",
        ge=0.5,
        le=80.0
    )
    tags: list[str] = Field(
        default_factory=list,
        description="Relevant tags for categorization",
        max_length=5
    )
    assignee: str | None = Field(
        None,
        description="Person assigned to the task"
    )


# Schema with nested objects
class Address(BaseModel):
    """Address information"""
    street: str = Field(min_length=3, max_length=100)
    city: str = Field(min_length=2, max_length=50)
    country: str = Field(
        pattern="^[A-Z]{2}$",
        description="ISO 3166-1 alpha-2 country code"
    )
    postal_code: str = Field(
        pattern=r"^\d{5}(-\d{4})?$",
        description="ZIP or ZIP+4 format"
    )


class CustomerExtraction(BaseModel):
    """Extract customer information from text"""
    
    # Basic info
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr = Field(description="Valid email address")
    
    # Contact info
    phone: str | None = Field(
        None,
        pattern=r"^\+?1?\d{9,15}$",
        description="Phone number in international format"
    )
    
    # Address (nested object)
    address: Address | None = None
    
    # Status
    status: Literal["active", "inactive", "pending"] = "pending"
    customer_type: Literal["individual", "business"] = "individual"


# Schema with complex validation rules
class TicketClassification(BaseModel):
    """Classify support tickets"""
    
    ticket_id: str = Field(
        pattern=r"^TICKET-\d{6}$",
        description="Ticket ID format: TICKET-123456"
    )
    
    severity: Literal["low", "medium", "high", "critical"] = Field(
        description="Issue severity level"
    )
    
    category: Literal[
        "technical",
        "billing",
        "feature_request",
        "bug_report",
        "general_inquiry"
    ] = Field(description="Ticket category")
    
    sentiment: Literal["positive", "neutral", "negative"] = Field(
        description="Customer sentiment"
    )
    
    requires_escalation: bool = Field(
        description="Whether ticket needs escalation to senior support"
    )
    
    confidence_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Model's confidence in classification"
    )
    
    extracted_entities: list[str] = Field(
        default_factory=list,
        description="Extracted product names, features, or error codes",
        max_length=10
    )


def demonstrate_schemas():
    """Demonstrate schema usage"""
    
    print("=" * 60)
    print("Example 1: Schema Definitions")
    print("=" * 60)
    
    # Valid task V1
    print("\n1. Simple Task (V1):")
    task_v1 = TaskExtractionV1(
        title="Fix login bug",
        priority=4
    )
    print(f"   {task_v1.model_dump_json(indent=2)}")
    
    # Valid task V2
    print("\n2. Enhanced Task (V2):")
    task_v2 = TaskExtractionV2(
        title="Implement user dashboard",
        priority=3,
        category="feature",
        description="Create a dashboard showing user activity metrics",
        estimated_hours=16.0,
        tags=["frontend", "dashboard", "metrics"]
    )
    print(f"   {task_v2.model_dump_json(indent=2)}")
    
    # Customer with nested address
    print("\n3. Customer with Nested Address:")
    customer = CustomerExtraction(
        name="John Doe",
        email="john@example.com",
        phone="+12025551234",
        address=Address(
            street="123 Main St",
            city="Washington",
            country="US",
            postal_code="20001"
        ),
        status="active",
        customer_type="individual"
    )
    print(f"   {customer.model_dump_json(indent=2)}")
    
    # Ticket classification
    print("\n4. Ticket Classification:")
    ticket = TicketClassification(
        ticket_id="TICKET-000123",
        severity="high",
        category="bug_report",
        sentiment="negative",
        requires_escalation=True,
        confidence_score=0.92,
        extracted_entities=["authentication", "login_page", "500_error"]
    )
    print(f"   {ticket.model_dump_json(indent=2)}")
    
    # Schema info
    print("\n5. Schema JSON Schema:")
    print(f"   {TaskExtractionV2.model_json_schema()}")
    
    print("\n" + "=" * 60)
    print("All schemas validated successfully!")
    print("=" * 60)


if __name__ == "__main__":
    demonstrate_schemas()
