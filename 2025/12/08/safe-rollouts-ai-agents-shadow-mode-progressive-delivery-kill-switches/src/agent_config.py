"""Agent configuration with versioning support."""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional


class AgentConfig:
    """Agent configuration with versioning."""
    
    def __init__(self, config: Dict[str, Any]):
        self.version = config["version"]
        self.model = config["model"]
        self.prompt = config["prompt"]
        self.tools = config["tools"]
        self.policies = config.get("policies", {})
    
    @classmethod
    def load(cls, agent_name: str, version: str) -> "AgentConfig":
        """Load agent config from file."""
        config_path = Path(f"agents/{agent_name}/{version}.yaml")
        if not config_path.exists():
            raise FileNotFoundError(f"Config not found: {config_path}")
        
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        return cls(config)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "version": self.version,
            "model": self.model,
            "prompt": self.prompt,
            "tools": self.tools,
            "policies": self.policies
        }
