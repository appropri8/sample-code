"""Kill switch implementation for instant agent version rollback."""

import json
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime


class KillSwitch:
    """Manages kill switches for agent versions."""
    
    def __init__(self, config_path: str = "kill_switches.json"):
        self.config_path = Path(config_path)
        self._load_config()
    
    def _load_config(self):
        """Load kill switch config from file."""
        if self.config_path.exists():
            with open(self.config_path, "r") as f:
                self.config = json.load(f)
        else:
            self.config = {
                "global_switches": {},
                "feature_switches": {},
                "tenant_switches": {}
            }
            self._save_config()
    
    def _save_config(self):
        """Save kill switch config to file."""
        with open(self.config_path, "w") as f:
            json.dump(self.config, f, indent=2)
    
    def is_killed(self, agent_name: str, version: str, feature: Optional[str] = None, tenant: Optional[str] = None) -> bool:
        """Check if a version is killed."""
        # Check global switch
        global_key = f"{agent_name}:{version}"
        if global_key in self.config["global_switches"]:
            if self.config["global_switches"][global_key].get("enabled", False):
                return True
        
        # Check feature switch
        if feature:
            feature_key = f"{agent_name}:{version}:{feature}"
            if feature_key in self.config["feature_switches"]:
                if self.config["feature_switches"][feature_key].get("enabled", False):
                    return True
        
        # Check tenant switch
        if tenant:
            tenant_key = f"{agent_name}:{version}:{tenant}"
            if tenant_key in self.config["tenant_switches"]:
                if self.config["tenant_switches"][tenant_key].get("enabled", False):
                    return True
        
        return False
    
    def kill_version(
        self,
        agent_name: str,
        version: str,
        reason: str,
        feature: Optional[str] = None,
        tenant: Optional[str] = None
    ):
        """Kill a version (enable kill switch)."""
        if feature:
            key = f"{agent_name}:{version}:{feature}"
            self.config["feature_switches"][key] = {
                "enabled": True,
                "reason": reason,
                "killed_at": datetime.utcnow().isoformat()
            }
        elif tenant:
            key = f"{agent_name}:{version}:{tenant}"
            self.config["tenant_switches"][key] = {
                "enabled": True,
                "reason": reason,
                "killed_at": datetime.utcnow().isoformat()
            }
        else:
            key = f"{agent_name}:{version}"
            self.config["global_switches"][key] = {
                "enabled": True,
                "reason": reason,
                "killed_at": datetime.utcnow().isoformat()
            }
        
        self._save_config()
    
    def unkill_version(
        self,
        agent_name: str,
        version: str,
        feature: Optional[str] = None,
        tenant: Optional[str] = None
    ):
        """Unkill a version (disable kill switch)."""
        if feature:
            key = f"{agent_name}:{version}:{feature}"
            if key in self.config["feature_switches"]:
                del self.config["feature_switches"][key]
        elif tenant:
            key = f"{agent_name}:{version}:{tenant}"
            if key in self.config["tenant_switches"]:
                del self.config["tenant_switches"][key]
        else:
            key = f"{agent_name}:{version}"
            if key in self.config["global_switches"]:
                del self.config["global_switches"][key]
        
        self._save_config()
