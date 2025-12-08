"""Quality gates for agent version rollouts."""

import yaml
from typing import Dict, Any, List
from pathlib import Path


class QualityGate:
    """Represents a single quality gate."""
    
    def __init__(self, config: Dict[str, Any]):
        self.name = config["name"]
        self.type = config["type"]
        self.metric = config.get("metric")
        self.threshold = config.get("threshold")
        self.operator = config.get("operator", ">=")
        self.test_suite = config.get("test_suite")
        self.min_pass_rate = config.get("min_pass_rate", 1.0)
    
    def check(self, metrics: Dict[str, Any]) -> tuple[bool, str]:
        """
        Check if gate passes.
        
        Returns (passed, message)
        """
        if self.type == "threshold":
            return self._check_threshold(metrics)
        elif self.type == "test_suite":
            return self._check_test_suite(metrics)
        else:
            return False, f"Unknown gate type: {self.type}"
    
    def _check_threshold(self, metrics: Dict[str, Any]) -> tuple[bool, str]:
        """Check threshold gate."""
        if self.metric not in metrics:
            return False, f"Metric {self.metric} not found"
        
        value = metrics[self.metric]
        threshold = self.threshold
        
        if self.operator == ">=":
            passed = value >= threshold
        elif self.operator == "<=":
            passed = value <= threshold
        elif self.operator == ">":
            passed = value > threshold
        elif self.operator == "<":
            passed = value < threshold
        elif self.operator == "==":
            passed = value == threshold
        else:
            return False, f"Unknown operator: {self.operator}"
        
        if passed:
            return True, f"{self.name}: {value} {self.operator} {threshold}"
        else:
            return False, f"{self.name}: {value} {self.operator} {threshold} (FAILED)"
    
    def _check_test_suite(self, metrics: Dict[str, Any]) -> tuple[bool, str]:
        """Check test suite gate."""
        if self.test_suite not in metrics:
            return False, f"Test suite {self.test_suite} not found"
        
        test_results = metrics[self.test_suite]
        total = len(test_results)
        passed = sum(1 for r in test_results if r["passed"])
        pass_rate = passed / total if total > 0 else 0
        
        if pass_rate >= self.min_pass_rate:
            return True, f"{self.name}: {passed}/{total} tests passed ({pass_rate:.1%})"
        else:
            return False, f"{self.name}: {passed}/{total} tests passed ({pass_rate:.1%}) < {self.min_pass_rate:.1%} (FAILED)"


class QualityGateChecker:
    """Checks quality gates for agent versions."""
    
    def __init__(self, gates_config_path: str):
        with open(gates_config_path, "r") as f:
            config = yaml.safe_load(f)
        
        self.gates = [QualityGate(g) for g in config["gates"]]
    
    def check_all(self, metrics: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Check all gates.
        
        Returns (all_passed, messages)
        """
        results = []
        all_passed = True
        
        for gate in self.gates:
            passed, message = gate.check(metrics)
            results.append(message)
            if not passed:
                all_passed = False
        
        return all_passed, results
