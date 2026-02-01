"""Tool registry with JSON schema validation. Deny by default."""

import jsonschema
from typing import Any, Optional

# Tool registry: name -> { schema, allowed_roles, requires_approval }
TOOL_REGISTRY: dict[str, dict[str, Any]] = {
    "read_file": {
        "schema": {
            "type": "object",
            "properties": {"path": {"type": "string", "maxLength": 512}},
            "required": ["path"],
            "additionalProperties": False,
        },
        "allowed_roles": ["read_only_agent", "action_agent"],
        "requires_approval": False,
    },
    "search": {
        "schema": {
            "type": "object",
            "properties": {"query": {"type": "string", "maxLength": 1024}},
            "required": ["query"],
            "additionalProperties": False,
        },
        "allowed_roles": ["read_only_agent", "action_agent"],
        "requires_approval": False,
    },
    "write_file": {
        "schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "maxLength": 512},
                "content": {"type": "string", "maxLength": 1024 * 1024},
            },
            "required": ["path", "content"],
            "additionalProperties": False,
        },
        "allowed_roles": ["action_agent"],
        "requires_approval": True,
    },
    "delete_file": {
        "schema": {
            "type": "object",
            "properties": {"path": {"type": "string", "maxLength": 512}},
            "required": ["path"],
            "additionalProperties": False,
        },
        "allowed_roles": ["action_agent"],
        "requires_approval": True,
    },
}


def get_tool(tool_name: str) -> Optional[dict]:
    """Return tool config if registered, else None (deny by default)."""
    return TOOL_REGISTRY.get(tool_name)


def validate_arguments(tool_name: str, arguments: dict) -> tuple:
    """
    Validate arguments against tool schema.
    Returns (valid, error_message).
    """
    tool = get_tool(tool_name)
    if not tool:
        return False, f"Tool '{tool_name}' not in registry (deny by default)"
    schema = tool.get("schema")
    if not schema:
        return True, None
    try:
        jsonschema.validate(instance=arguments, schema=schema)
        return True, None
    except jsonschema.ValidationError as e:
        return False, getattr(e, "message", None) or str(e)
