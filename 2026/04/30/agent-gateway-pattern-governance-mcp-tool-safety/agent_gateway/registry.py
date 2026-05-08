import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    description: str
    risk_tier: str
    auth_scope: str
    approval_required: bool
    input_schema: dict
    output_schema: dict
    mcp_server: str
    mcp_tool: str

    @classmethod
    def from_dict(cls, data):
        return cls(
            name=data["name"],
            description=data["description"],
            risk_tier=data["riskTier"],
            auth_scope=data["authScope"],
            approval_required=bool(data.get("approvalRequired", False)),
            input_schema=data["inputSchema"],
            output_schema=data["outputSchema"],
            mcp_server=data["mcpServer"],
            mcp_tool=data["mcpTool"],
        )


class ToolRegistry:
    def __init__(self, tools):
        self._tools = {tool.name: tool for tool in tools}

    @classmethod
    def from_file(cls, path):
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(ToolDefinition.from_dict(item) for item in raw["tools"])

    def get(self, name):
        try:
            return self._tools[name]
        except KeyError as exc:
            raise KeyError(f"unknown tool: {name}") from exc

