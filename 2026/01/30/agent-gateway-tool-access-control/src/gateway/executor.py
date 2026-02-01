"""Mock tool executor. In production, call real adapters with secrets injected at execution time."""

from typing import Any, Optional


def execute_tool(tool: str, arguments: dict, _secrets: Optional[dict] = None) -> Any:
    """
    Execute tool with arguments. Secrets are injected at execution time (not passed from agent).
    This is a mock: real implementation would call tool adapters.
    """
    if tool == "read_file":
        return {"content": f"[mock read of {arguments.get('path', '')}]", "path": arguments.get("path")}
    if tool == "search":
        return {"results": [f"[mock result for query: {arguments.get('query', '')}]"], "count": 1}
    if tool == "write_file":
        return {"written": arguments.get("path"), "size": len(str(arguments.get("content", "")))}
    if tool == "delete_file":
        return {"deleted": arguments.get("path")}
    return {"error": f"Unknown tool: {tool}"}
