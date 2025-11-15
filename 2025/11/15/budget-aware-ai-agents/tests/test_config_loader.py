"""Tests for configuration loader."""

import pytest
import tempfile
import os
from pathlib import Path
from src.config_loader import load_budget_config
from src.budgets import RunBudget


class TestConfigLoader:
    """Tests for configuration loader."""
    
    def test_load_budget_config(self):
        # Create temporary config file
        config_content = """
budgets:
  quick_answer:
    max_steps: 5
    max_tokens: 2000
    max_seconds: 10
    max_nested_tool_calls: 2
  
  deep_research:
    max_steps: 20
    max_tokens: 50000
    max_seconds: 60
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            temp_path = f.name
        
        try:
            budgets = load_budget_config(temp_path)
            
            assert "quick_answer" in budgets
            assert "deep_research" in budgets
            
            assert isinstance(budgets["quick_answer"], RunBudget)
            assert budgets["quick_answer"].max_steps == 5
            assert budgets["quick_answer"].max_tokens == 2000
            
            assert budgets["deep_research"].max_steps == 20
            assert budgets["deep_research"].max_tokens == 50000
        finally:
            os.unlink(temp_path)
    
    def test_load_budget_config_not_found(self):
        with pytest.raises(FileNotFoundError):
            load_budget_config("nonexistent.yaml")

