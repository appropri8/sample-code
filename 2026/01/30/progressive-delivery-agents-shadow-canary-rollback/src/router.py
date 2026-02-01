"""
Feature-flagged router: shadow execution, canary percentage rollout, instant rollback.

- shadow: new agent runs on live traffic but cannot take actions; only baseline executes.
- canary: canary_percent of traffic goes to new agent; rest to baseline.
- baseline (rollback): 100% traffic to baseline; single flag.
"""

import hashlib
import random
from dataclasses import dataclass
from enum import Enum
from typing import Literal


class RouterMode(str, Enum):
    BASELINE = "baseline"   # 100% baseline (rollback)
    SHADOW = "shadow"       # New agent runs in shadow; no actions
    CANARY = "canary"       # canary_percent to new agent


@dataclass
class RouterConfig:
    mode: RouterMode
    canary_percent: float = 0.0  # 0–100; used when mode == CANARY

    def should_use_new_agent(self, request_id: str) -> bool:
        """Whether this request should be sent to the new agent (for execution or shadow)."""
        if self.mode == RouterMode.BASELINE:
            return False
        if self.mode == RouterMode.SHADOW:
            return True  # All traffic also goes to new agent in shadow (no actions)
        if self.mode == RouterMode.CANARY:
            # Deterministic by request_id so same user gets same version
            h = int(hashlib.sha256(request_id.encode()).hexdigest(), 16)
            return (h % 100) < self.canary_percent
        return False

    def new_agent_can_execute(self) -> bool:
        """Whether the new agent is allowed to execute actions (vs shadow-only)."""
        return self.mode == RouterMode.CANARY


def route(request_id: str, config: RouterConfig) -> Literal["baseline", "new"]:
    """
    Route a request to baseline or new agent.
    Returns "baseline" or "new". When mode is SHADOW, both run but only baseline executes.
    """
    if config.mode == RouterMode.BASELINE:
        return "baseline"
    if config.mode == RouterMode.SHADOW:
        # Caller runs both; this returns who "owns" execution (baseline). Shadow runner sends copy to new.
        return "baseline"
    if config.mode == RouterMode.CANARY and config.should_use_new_agent(request_id):
        return "new"
    return "baseline"


# Example: instant rollback = set config to baseline
def rollback_config() -> RouterConfig:
    return RouterConfig(mode=RouterMode.BASELINE, canary_percent=0.0)
