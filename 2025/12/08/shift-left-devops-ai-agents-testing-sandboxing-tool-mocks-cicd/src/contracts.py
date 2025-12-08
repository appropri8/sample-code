"""Tool contracts for agent validation."""

TOOL_CONTRACT = {
    "type": "object",
    "properties": {
        "tool_name": {
            "type": "string",
            "enum": ["search_database", "send_notification", "get_user_info"]
        },
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "maxLength": 500},
                "user_id": {"type": "string", "pattern": "^user_\\d+$"},
                "email": {"type": "string", "format": "email"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 100}
            },
            "required": ["query"]
        }
    },
    "required": ["tool_name", "parameters"]
}

POLICY_RULES = {
    "max_steps": 10,
    "forbidden_tools_in_test": ["/delete_user", "/delete_account"],
    "required_parameters": {
        "search_database": ["query", "limit"]
    },
    "no_pii_in_logs": True
}
