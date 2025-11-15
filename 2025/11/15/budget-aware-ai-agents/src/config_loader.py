"""Configuration loader for budgets."""

import yaml
from typing import Dict
from pathlib import Path
from .budgets import RunBudget


def load_budget_config(config_path: str) -> Dict[str, RunBudget]:
    """
    Load budget configuration from YAML file.
    
    Args:
        config_path: Path to YAML configuration file
    
    Returns:
        Dictionary mapping budget names to RunBudget objects
    
    Example YAML:
        budgets:
          quick_answer:
            max_steps: 5
            max_tokens: 2000
            max_seconds: 10
            max_nested_tool_calls: 2
    """
    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_file) as f:
        config = yaml.safe_load(f)
    
    budgets = {}
    for name, params in config.get("budgets", {}).items():
        budgets[name] = RunBudget(**params)
    
    return budgets

