"""
Shared schema definitions used across examples
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Literal
from datetime import datetime


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
