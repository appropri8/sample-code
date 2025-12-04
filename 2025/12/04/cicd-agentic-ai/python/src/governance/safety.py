"""Safety toggles and permissions for agents"""
import os
import yaml
from typing import Dict, Any, List


class SafetyToggles:
    """Environment-level safety toggles"""
    
    def __init__(self, config_path: str = None):
        self.env = os.getenv("ENVIRONMENT", "production")
        if config_path:
            self.config = self._load_config(config_path)
        else:
            self.config = self._default_config()
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load config from YAML"""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def _default_config(self) -> Dict[str, Any]:
        """Default config"""
        return {
            "agent_roles": {
                "support_agent": {
                    "allowed_tools": ["search_kb", "create_ticket", "get_user_info"],
                    "forbidden_tools": ["delete_user", "update_billing", "escalate_critical"]
                },
                "billing_agent": {
                    "allowed_tools": ["get_user_info", "update_billing", "get_payment_history"],
                    "forbidden_tools": ["delete_user", "escalate_critical"]
                }
            },
            "environments": {
                "production": {
                    "write_mode": False,
                    "max_cost_per_request": 1.0,
                    "max_latency_ms": 10000
                },
                "staging": {
                    "write_mode": True,
                    "max_cost_per_request": 5.0,
                    "max_latency_ms": 30000
                }
            }
        }
    
    def can_write(self, agent_role: str) -> bool:
        """Check if agent can write"""
        if not self.config["environments"][self.env]["write_mode"]:
            return False
        return True
    
    def can_call_tool(self, agent_role: str, tool_name: str) -> bool:
        """Check if agent can call tool"""
        role_config = self.config["agent_roles"].get(agent_role, {})
        
        # Check forbidden
        if tool_name in role_config.get("forbidden_tools", []):
            return False
        
        # Check allowed
        allowed = role_config.get("allowed_tools", [])
        if "*" in allowed:
            return True
        if tool_name in allowed:
            return True
        
        return False
    
    def get_max_cost(self) -> float:
        """Get max cost per request"""
        return self.config["environments"][self.env]["max_cost_per_request"]
    
    def get_max_latency(self) -> int:
        """Get max latency in ms"""
        return self.config["environments"][self.env]["max_latency_ms"]

