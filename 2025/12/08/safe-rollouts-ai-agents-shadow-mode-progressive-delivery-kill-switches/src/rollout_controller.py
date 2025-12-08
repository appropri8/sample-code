"""Progressive rollout controller for agent versions."""

import time
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

from .agent_factory import create_agent


class RolloutStage(Enum):
    SHADOW = "shadow"
    CANARY_1_PCT = "canary_1pct"
    CANARY_5_PCT = "canary_5pct"
    CANARY_25_PCT = "canary_25pct"
    CANARY_50_PCT = "canary_50pct"
    FULL = "full"
    ROLLED_BACK = "rolled_back"


@dataclass
class RolloutThresholds:
    """Thresholds for automatic rollback."""
    max_error_rate_increase: float = 0.05
    max_latency_increase_ms: int = 200
    max_cost_increase_percent: float = 20
    max_policy_violations: int = 0


class RolloutController:
    """Manages progressive rollout of agent versions."""
    
    def __init__(
        self,
        agent_name: str,
        current_version: str,
        candidate_version: str,
        thresholds: RolloutThresholds
    ):
        self.agent_name = agent_name
        self.current_version = current_version
        self.candidate_version = candidate_version
        self.thresholds = thresholds
        self.stage = RolloutStage.SHADOW
        self.stage_start_time = time.time()
        self.metrics_history = []
    
    def should_use_candidate(self, user_id: str) -> bool:
        """Determine if request should use candidate version."""
        if self.stage == RolloutStage.SHADOW:
            return False  # Shadow mode doesn't serve candidate
        
        if self.stage == RolloutStage.ROLLED_BACK:
            return False  # Rolled back, use current
        
        # Calculate percentage based on user_id hash
        user_hash = hash(user_id) % 100
        percentage = self._get_stage_percentage()
        
        return user_hash < percentage
    
    def _get_stage_percentage(self) -> int:
        """Get traffic percentage for current stage."""
        stage_percentages = {
            RolloutStage.CANARY_1_PCT: 1,
            RolloutStage.CANARY_5_PCT: 5,
            RolloutStage.CANARY_25_PCT: 25,
            RolloutStage.CANARY_50_PCT: 50,
            RolloutStage.FULL: 100
        }
        return stage_percentages.get(self.stage, 0)
    
    def record_metrics(
        self,
        version: str,
        error: bool,
        latency_ms: float,
        cost: float,
        policy_violations: int
    ):
        """Record metrics for a request."""
        self.metrics_history.append({
            "timestamp": time.time(),
            "version": version,
            "error": error,
            "latency_ms": latency_ms,
            "cost": cost,
            "policy_violations": policy_violations
        })
        
        # Keep only recent metrics (last hour)
        cutoff = time.time() - 3600
        self.metrics_history = [
            m for m in self.metrics_history
            if m["timestamp"] > cutoff
        ]
    
    def evaluate_and_advance(self) -> bool:
        """
        Evaluate metrics and advance to next stage if safe.
        
        Returns True if advanced, False if rolled back.
        """
        if self.stage == RolloutStage.SHADOW:
            # Shadow mode: just collect metrics, don't advance automatically
            return False
        
        if self.stage == RolloutStage.FULL:
            # Already at 100%, nothing to do
            return False
        
        # Check if we should roll back
        if self._should_rollback():
            self.stage = RolloutStage.ROLLED_BACK
            return False
        
        # Check if we've been in this stage long enough
        stage_duration = time.time() - self.stage_start_time
        min_stage_duration = 3600  # 1 hour minimum per stage
        
        if stage_duration < min_stage_duration:
            return False  # Not enough time in this stage
        
        # Advance to next stage
        self._advance_stage()
        return True
    
    def _should_rollback(self) -> bool:
        """Check if metrics indicate we should roll back."""
        if not self.metrics_history:
            return False
        
        # Calculate metrics for candidate version
        candidate_metrics = [
            m for m in self.metrics_history
            if m["version"] == self.candidate_version
        ]
        
        if not candidate_metrics:
            return False
        
        current_metrics = [
            m for m in self.metrics_history
            if m["version"] == self.current_version
        ]
        
        if not current_metrics:
            return True  # No baseline, roll back
        
        # Calculate averages
        candidate_error_rate = sum(m["error"] for m in candidate_metrics) / len(candidate_metrics)
        current_error_rate = sum(m["error"] for m in current_metrics) / len(current_metrics)
        
        candidate_avg_latency = sum(m["latency_ms"] for m in candidate_metrics) / len(candidate_metrics)
        current_avg_latency = sum(m["latency_ms"] for m in current_metrics) / len(current_metrics)
        
        candidate_avg_cost = sum(m["cost"] for m in candidate_metrics) / len(candidate_metrics)
        current_avg_cost = sum(m["cost"] for m in current_metrics) / len(current_metrics)
        
        candidate_violations = sum(m["policy_violations"] for m in candidate_metrics)
        
        # Check thresholds
        if candidate_error_rate - current_error_rate > self.thresholds.max_error_rate_increase:
            return True
        
        if candidate_avg_latency - current_avg_latency > self.thresholds.max_latency_increase_ms:
            return True
        
        if (candidate_avg_cost - current_avg_cost) / current_avg_cost > self.thresholds.max_cost_increase_percent / 100:
            return True
        
        if candidate_violations > self.thresholds.max_policy_violations:
            return True
        
        return False
    
    def _advance_stage(self):
        """Advance to next rollout stage."""
        stage_order = [
            RolloutStage.SHADOW,
            RolloutStage.CANARY_1_PCT,
            RolloutStage.CANARY_5_PCT,
            RolloutStage.CANARY_25_PCT,
            RolloutStage.CANARY_50_PCT,
            RolloutStage.FULL
        ]
        
        current_index = stage_order.index(self.stage)
        if current_index < len(stage_order) - 1:
            self.stage = stage_order[current_index + 1]
            self.stage_start_time = time.time()
