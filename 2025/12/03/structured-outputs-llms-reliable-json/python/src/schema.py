"""Schema definitions using Pydantic."""
from pydantic import BaseModel, Field
from enum import Enum


class Category(str, Enum):
    """Task category enum."""
    BUG = "bug"
    FEATURE = "feature"
    QUESTION = "question"
    OTHER = "other"


class TaskTriage(BaseModel):
    """Task triage schema for categorizing and prioritizing issues."""
    category: Category = Field(description="Category of the task")
    priority: int = Field(ge=1, le=5, description="Priority from 1 (low) to 5 (critical)")
    needs_human: bool = Field(description="Whether this task requires human intervention")
    summary: str | None = Field(None, description="Brief summary of the issue")
    
    class Config:
        extra = "forbid"  # Reject extra fields


class UserInfo(BaseModel):
    """User information extraction schema."""
    name: str = Field(description="User's full name")
    email: str = Field(description="User's email address")
    age: int | None = Field(None, ge=0, le=150, description="User's age if mentioned")
    
    class Config:
        extra = "forbid"

