"""
Cost and rate limiting for agent actions.
Enforces per-agent and per-tool budgets to prevent cost explosions.
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import time
from collections import defaultdict
import yaml


class CostLimiter:
    """Enforce cost and rate limits for agent actions."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize cost limiter.
        
        Args:
            config: Configuration dict with agent budgets and limits
        """
        self.config = config
        self.daily_spend = defaultdict(float)
        self.tool_call_counts = defaultdict(lambda: defaultdict(int))
        self.tool_call_times = defaultdict(lambda: defaultdict(list))
        self.last_reset = datetime.utcnow().date()
    
    def check_budget(
        self,
        agent_name: str,
        tool_name: str,
        estimated_cost: float
    ) -> tuple[bool, str]:
        """
        Check if action is within budget. Returns (allowed, reason).
        
        Args:
            agent_name: Name of the agent
            tool_name: Name of the tool
            estimated_cost: Estimated cost in USD
        
        Returns:
            Tuple of (allowed, reason)
        """
        # Reset daily counters if new day
        if datetime.utcnow().date() > self.last_reset:
            self.daily_spend.clear()
            self.tool_call_counts.clear()
            self.tool_call_times.clear()
            self.last_reset = datetime.utcnow().date()
        
        agent_config = self.config["agents"].get(agent_name, {})
        
        # Check daily budget
        daily_budget = agent_config.get("daily_budget_usd", 0)
        current_spend = self.daily_spend[agent_name]
        
        if current_spend + estimated_cost > daily_budget:
            return False, f"Daily budget exceeded: ${current_spend:.2f} / ${daily_budget:.2f}"
        
        # Check per-request max
        per_request_max = agent_config.get("per_request_max_usd", 0)
        if estimated_cost > per_request_max:
            return False, f"Per-request cost ${estimated_cost:.2f} exceeds max ${per_request_max:.2f}"
        
        # Check tool-specific limits
        tool_limits = agent_config.get("per_tool_limits", {}).get(tool_name, {})
        
        # Check max calls per hour
        max_calls_per_hour = tool_limits.get("max_calls_per_hour")
        if max_calls_per_hour:
            now = time.time()
            hour_ago = now - 3600
            
            # Clean old timestamps
            self.tool_call_times[agent_name][tool_name] = [
                t for t in self.tool_call_times[agent_name][tool_name]
                if t > hour_ago
            ]
            
            calls_in_hour = len(self.tool_call_times[agent_name][tool_name])
            if calls_in_hour >= max_calls_per_hour:
                return False, f"Rate limit: {calls_in_hour} calls in last hour (max: {max_calls_per_hour})"
        
        # Check max calls per day
        max_calls_per_day = tool_limits.get("max_calls_per_day")
        if max_calls_per_day:
            calls_today = self.tool_call_counts[agent_name][tool_name]
            if calls_today >= max_calls_per_day:
                return False, f"Daily limit: {calls_today} calls today (max: {max_calls_per_day})"
        
        return True, "allowed"
    
    def record_cost(
        self,
        agent_name: str,
        tool_name: str,
        actual_cost: float
    ):
        """
        Record actual cost after action.
        
        Args:
            agent_name: Name of the agent
            tool_name: Name of the tool
            actual_cost: Actual cost in USD
        """
        self.daily_spend[agent_name] += actual_cost
        self.tool_call_counts[agent_name][tool_name] += 1
        self.tool_call_times[agent_name][tool_name].append(time.time())
        
        # Check if approaching budget threshold
        agent_config = self.config["agents"].get(agent_name, {})
        daily_budget = agent_config.get("daily_budget_usd", 0)
        threshold = self.config["alerts"]["budget_threshold_percent"] / 100.0
        
        if daily_budget > 0 and self.daily_spend[agent_name] >= daily_budget * threshold:
            self._send_alert(
                f"Agent {agent_name} at {self.daily_spend[agent_name]/daily_budget*100:.1f}% of daily budget"
            )
    
    def _send_alert(self, message: str):
        """Send alert (implement based on your alerting system)."""
        print(f"ALERT: {message}")
        # In production, send to your alerting system (PagerDuty, Slack, etc.)


def load_config(config_path: str) -> Dict[str, Any]:
    """Load cost limits configuration from YAML file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


# Example usage
if __name__ == "__main__":
    # Load config
    config = {
        "agents": {
            "ops-agent": {
                "daily_budget_usd": 100.0,
                "per_request_max_usd": 1.0,
                "per_tool_limits": {
                    "scale_deployment": {
                        "max_calls_per_hour": 10,
                        "cost_per_call_usd": 0.01
                    }
                }
            }
        },
        "alerts": {
            "budget_threshold_percent": 80
        }
    }
    
    cost_limiter = CostLimiter(config)
    
    # Check budget before executing tool
    allowed, reason = cost_limiter.check_budget(
        agent_name="ops-agent",
        tool_name="scale_deployment",
        estimated_cost=0.01
    )
    
    if not allowed:
        print(f"Cost limit exceeded: {reason}")
    else:
        print("Budget check passed - executing tool")
        # Execute tool...
        # Record actual cost
        cost_limiter.record_cost(
            agent_name="ops-agent",
            tool_name="scale_deployment",
            actual_cost=0.01
        )
