"""Factory for creating agents from versioned configs."""

from .agent_config import AgentConfig
from .agent import Agent


def create_agent(agent_name: str, version: str) -> Agent:
    """Create an agent instance from a versioned config."""
    config = AgentConfig.load(agent_name, version)
    return Agent(config)
