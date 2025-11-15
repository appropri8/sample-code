"""Tool registry with metadata for risk assessment and permissions"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from enum import Enum
import json


class RiskLevel(str, Enum):
    """Risk levels for tools"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class Tool:
    """Represents a tool with metadata"""
    name: str
    description: str
    schema: Dict[str, Any]  # JSON schema
    risk_level: RiskLevel
    allowed_roles: List[str]
    requires_approval: bool = False
    enabled: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "description": self.description,
            "schema": self.schema,
            "risk_level": self.risk_level.value,
            "allowed_roles": self.allowed_roles,
            "requires_approval": self.requires_approval,
            "enabled": self.enabled
        }


# Tool registry
TOOL_REGISTRY: Dict[str, Tool] = {
    "read_ticket": Tool(
        name="read_ticket",
        description="Read a support ticket",
        schema={
            "type": "object",
            "properties": {
                "ticket_id": {
                    "type": "string",
                    "description": "The ticket ID to read"
                }
            },
            "required": ["ticket_id"]
        },
        risk_level=RiskLevel.LOW,
        allowed_roles=["support_agent", "support_manager", "readonly"]
    ),
    "add_comment": Tool(
        name="add_comment",
        description="Add a comment to a support ticket",
        schema={
            "type": "object",
            "properties": {
                "ticket_id": {
                    "type": "string",
                    "description": "The ticket ID"
                },
                "comment": {
                    "type": "string",
                    "description": "The comment text",
                    "minLength": 1
                }
            },
            "required": ["ticket_id", "comment"]
        },
        risk_level=RiskLevel.LOW,
        allowed_roles=["support_agent", "support_manager"]
    ),
    "close_ticket": Tool(
        name="close_ticket",
        description="Close a support ticket",
        schema={
            "type": "object",
            "properties": {
                "ticket_id": {
                    "type": "string",
                    "description": "The ticket ID to close"
                },
                "reason": {
                    "type": "string",
                    "description": "Reason for closing",
                    "minLength": 10
                }
            },
            "required": ["ticket_id", "reason"]
        },
        risk_level=RiskLevel.HIGH,
        allowed_roles=["support_manager"],
        requires_approval=True
    )
}


def get_tool(tool_name: str) -> Optional[Tool]:
    """Get a tool from the registry"""
    return TOOL_REGISTRY.get(tool_name)


def get_tools_for_role(role: str) -> List[Tool]:
    """Get all tools allowed for a role"""
    return [
        tool for tool in TOOL_REGISTRY.values()
        if role in tool.allowed_roles and tool.enabled
    ]


def is_tool_allowed(tool_name: str, role: str) -> bool:
    """Check if a tool is allowed for a role"""
    tool = get_tool(tool_name)
    if not tool:
        return False
    if not tool.enabled:
        return False
    return role in tool.allowed_roles


def disable_tool(tool_name: str):
    """Disable a tool immediately"""
    if tool_name in TOOL_REGISTRY:
        TOOL_REGISTRY[tool_name].enabled = False


def enable_tool(tool_name: str):
    """Enable a tool"""
    if tool_name in TOOL_REGISTRY:
        TOOL_REGISTRY[tool_name].enabled = True

