"""Canary deployment for gradual rollout"""
import random
from typing import Dict, Any
from datetime import datetime
import logging


class CanaryDeployment:
    """Canary deployment: route percentage of traffic to new version"""
    
    def __init__(
        self,
        baseline_workflow,
        candidate_workflow,
        canary_percentage: float = 0.01,  # 1%
        rollback_conditions: Dict[str, Any] = None
    ):
        self.baseline = baseline_workflow
        self.candidate = candidate_workflow
        self.canary_pct = canary_percentage
        self.rollback_conditions = rollback_conditions or {
            "error_rate_threshold": 0.05,  # 5%
            "latency_threshold_ms": 10000,
            "cost_threshold_multiplier": 2.0
        }
        self.metrics = {
            "canary_requests": 0,
            "canary_errors": 0,
            "canary_latency_sum": 0,
            "canary_cost_sum": 0,
            "baseline_requests": 0,
            "baseline_errors": 0,
            "baseline_latency_sum": 0,
            "baseline_cost_sum": 0
        }
        self.logger = logging.getLogger(__name__)
        self.rolled_back = False
    
    def route(self, input: Dict[str, Any]) -> Dict[str, Any]:
        """Route request to baseline or canary"""
        if self.rolled_back:
            return self.baseline.execute(input)
        
        use_canary = random.random() < self.canary_pct
        
        if use_canary:
            return self._run_canary(input)
        else:
            return self._run_baseline(input)
    
    def _run_baseline(self, input: Dict[str, Any]) -> Dict[str, Any]:
        """Run baseline workflow"""
        try:
            result = self.baseline.execute(input)
            self.metrics["baseline_requests"] += 1
            self.metrics["baseline_latency_sum"] += result.get("latency_ms", 0)
            self.metrics["baseline_cost_sum"] += result.get("cost", 0)
            return result
        except Exception as e:
            self.metrics["baseline_errors"] += 1
            raise
    
    def _run_canary(self, input: Dict[str, Any]) -> Dict[str, Any]:
        """Run canary and check rollback conditions"""
        try:
            result = self.candidate.execute(input)
            
            # Track metrics
            self.metrics["canary_requests"] += 1
            self.metrics["canary_latency_sum"] += result.get("latency_ms", 0)
            self.metrics["canary_cost_sum"] += result.get("cost", 0)
            
            # Check rollback conditions
            if self._should_rollback():
                self.logger.warning("Canary rollback triggered")
                self.rolled_back = True
                # Rollback: route to baseline
                return self.baseline.execute(input)
            
            return result
        except Exception as e:
            self.metrics["canary_errors"] += 1
            self.logger.error(f"Canary error: {e}")
            
            if self._should_rollback():
                self.rolled_back = True
                return self.baseline.execute(input)
            
            raise
    
    def _should_rollback(self) -> bool:
        """Check if canary should rollback"""
        if self.metrics["canary_requests"] < 10:
            return False  # Need minimum samples
        
        error_rate = (
            self.metrics["canary_errors"] / 
            self.metrics["canary_requests"]
        )
        if error_rate > self.rollback_conditions["error_rate_threshold"]:
            return True
        
        if self.metrics["canary_requests"] > 0:
            avg_latency = (
                self.metrics["canary_latency_sum"] / 
                self.metrics["canary_requests"]
            )
            if avg_latency > self.rollback_conditions["latency_threshold_ms"]:
                return True
            
            # Check cost multiplier
            if self.metrics["baseline_requests"] > 0:
                baseline_avg_cost = (
                    self.metrics["baseline_cost_sum"] / 
                    self.metrics["baseline_requests"]
                )
                canary_avg_cost = (
                    self.metrics["canary_cost_sum"] / 
                    self.metrics["canary_requests"]
                )
                if baseline_avg_cost > 0:
                    cost_multiplier = canary_avg_cost / baseline_avg_cost
                    if cost_multiplier > self.rollback_conditions["cost_threshold_multiplier"]:
                        return True
        
        return False
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get deployment metrics"""
        return {
            "canary": {
                "requests": self.metrics["canary_requests"],
                "errors": self.metrics["canary_errors"],
                "error_rate": (
                    self.metrics["canary_errors"] / self.metrics["canary_requests"]
                    if self.metrics["canary_requests"] > 0 else 0
                ),
                "avg_latency_ms": (
                    self.metrics["canary_latency_sum"] / self.metrics["canary_requests"]
                    if self.metrics["canary_requests"] > 0 else 0
                ),
                "avg_cost": (
                    self.metrics["canary_cost_sum"] / self.metrics["canary_requests"]
                    if self.metrics["canary_requests"] > 0 else 0
                )
            },
            "baseline": {
                "requests": self.metrics["baseline_requests"],
                "errors": self.metrics["baseline_errors"],
                "error_rate": (
                    self.metrics["baseline_errors"] / self.metrics["baseline_requests"]
                    if self.metrics["baseline_requests"] > 0 else 0
                ),
                "avg_latency_ms": (
                    self.metrics["baseline_latency_sum"] / self.metrics["baseline_requests"]
                    if self.metrics["baseline_requests"] > 0 else 0
                ),
                "avg_cost": (
                    self.metrics["baseline_cost_sum"] / self.metrics["baseline_requests"]
                    if self.metrics["baseline_requests"] > 0 else 0
                )
            },
            "rolled_back": self.rolled_back
        }

