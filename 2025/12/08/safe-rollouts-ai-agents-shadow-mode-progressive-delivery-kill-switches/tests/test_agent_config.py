"""Tests for agent configuration."""

import pytest
from pathlib import Path
from src.agent_config import AgentConfig


def test_load_config():
    """Test loading agent config from file."""
    config = AgentConfig.load("support-agent", "v1.3.2")
    
    assert config.version == "v1.3.2"
    assert config.model["provider"] == "openai"
    assert config.model["name"] == "gpt-4"
    assert len(config.tools) == 3
    assert config.policies["max_steps"] == 10


def test_config_to_dict():
    """Test converting config to dictionary."""
    config = AgentConfig.load("support-agent", "v1.3.2")
    config_dict = config.to_dict()
    
    assert config_dict["version"] == "v1.3.2"
    assert "model" in config_dict
    assert "prompt" in config_dict
    assert "tools" in config_dict


def test_config_not_found():
    """Test error when config file doesn't exist."""
    with pytest.raises(FileNotFoundError):
        AgentConfig.load("support-agent", "v999.9.9")
