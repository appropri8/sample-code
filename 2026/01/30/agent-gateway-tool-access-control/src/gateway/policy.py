"""Policy: allowlist by role, forbidden fields, requires_approval."""

from .registry import get_tool

# Role -> list of tools allowed
ROLE_ALLOWLIST: dict[str, list[str]] = {
    "read_only_agent": ["read_file", "search"],
    "action_agent": ["read_file", "search", "write_file", "delete_file"],
}

# Request body keys that must not be present (deny request)
FORBIDDEN_FIELDS = ["password", "api_key", "token", "secret"]


def allow_tool(role: str, tool_name: str) -> bool:
    """True if this role is allowed to call this tool."""
    allowed = ROLE_ALLOWLIST.get(role, [])
    return tool_name in allowed


def has_forbidden_fields(obj: dict) -> list[str]:
    """Return list of forbidden keys present in obj (recursive check on values)."""
    found: list[str] = []

    def check(d: dict, path: str = "") -> None:
        for k, v in d.items():
            key_lower = k.lower()
            if any(f in key_lower for f in FORBIDDEN_FIELDS):
                found.append(f"{path}.{k}" if path else k)
            if isinstance(v, dict):
                check(v, f"{path}.{k}" if path else k)
            elif isinstance(v, list):
                for i, item in enumerate(v):
                    if isinstance(item, dict):
                        check(item, f"{path}.{k}[{i}]")

    check(obj)
    return found


def requires_approval(tool_name: str) -> bool:
    """True if this tool requires human approval before execution."""
    tool = get_tool(tool_name)
    if not tool:
        return True  # unknown tool -> require approval
    return tool.get("requires_approval", True)
