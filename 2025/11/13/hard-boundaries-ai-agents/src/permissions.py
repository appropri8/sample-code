"""Tool and permission scoping for agents"""

from typing import List, Dict


TOOL_PERMISSIONS = {
    "user": ["search_kb", "create_ticket", "get_user_info"],
    "admin": ["search_kb", "create_ticket", "get_user_info", "delete_ticket", "modify_user"],
    "readonly": ["search_kb", "get_user_info"]
}

ENV_TOOLS = {
    "production": ["search_kb", "create_ticket"],
    "staging": ["search_kb", "create_ticket", "delete_ticket"],
    "development": ["search_kb", "create_ticket", "delete_ticket", "reset_database"]
}

TOOL_MATRIX = {
    "search_kb": {
        "roles": ["user", "admin", "readonly"],
        "environments": ["production", "staging", "development"],
        "rate_limit": "100/hour"
    },
    "delete_ticket": {
        "roles": ["admin"],
        "environments": ["staging", "development"],
        "rate_limit": "10/hour",
        "requires_approval": True
    },
    "reset_database": {
        "roles": ["admin"],
        "environments": ["development"],
        "rate_limit": "1/day",
        "requires_approval": True
    }
}


def get_tools_for_role(role: str) -> List[str]:
    """Get allowed tools for role"""
    return TOOL_PERMISSIONS.get(role, [])


def get_tools_for_env(env: str) -> List[str]:
    """Get allowed tools for environment"""
    return ENV_TOOLS.get(env, [])


def can_call_tool(tool_name: str, role: str, env: str) -> bool:
    """Check if tool can be called"""
    if tool_name not in TOOL_MATRIX:
        return False
    
    tool = TOOL_MATRIX[tool_name]
    return role in tool["roles"] and env in tool["environments"]


def get_tools_for_context(user_id: str, tenant_id: str, role: str, env: str) -> List[str]:
    """Get tools scoped to user and tenant"""
    base_tools = get_tools_for_role(role)
    env_tools = get_tools_for_env(env)
    
    # Intersection: must be in both
    allowed = set(base_tools) & set(env_tools)
    
    # Add tenant-specific tools
    if tenant_id == "enterprise":
        allowed.add("advanced_analytics")
    
    return list(allowed)


def log_tool_call(tool_name: str, params: dict, user_context: dict):
    """Log tool call for audit"""
    from datetime import datetime
    import json
    
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "tool": tool_name,
        "params": sanitize_params(params),
        "user_id": user_context.get("user_id"),
        "tenant_id": user_context.get("tenant_id"),
        "role": user_context.get("role"),
        "environment": user_context.get("environment")
    }
    
    print(f"AUDIT: {json.dumps(log_entry)}")


def sanitize_params(params: dict) -> dict:
    """Remove sensitive data from params"""
    sanitized = {}
    sensitive_keys = ["password", "api_key", "token", "secret"]
    
    for key, value in params.items():
        if any(sensitive in key.lower() for sensitive in sensitive_keys):
            sanitized[key] = "[REDACTED]"
        else:
            sanitized[key] = value
    
    return sanitized

