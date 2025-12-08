"""Example: Checking quality gates before rollout."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.quality_gates import QualityGateChecker


def main():
    """Run quality gates example."""
    print("=== Quality Gates Example ===\n")
    
    # Create checker
    checker = QualityGateChecker("quality_gates.yaml")
    
    # Simulate metrics from offline evals
    metrics = {
        "offline_quality_score": 0.87,
        "safety_checker_score": 0.96,
        "critical_scenarios": [
            {"name": "test_password_reset", "passed": True},
            {"name": "test_user_search", "passed": True},
            {"name": "test_email_sending", "passed": True}
        ],
        "p95_latency_ms": 1500,
        "avg_cost_per_request": 0.45
    }
    
    print("Metrics:")
    for key, value in metrics.items():
        if key != "critical_scenarios":
            print(f"  {key}: {value}")
        else:
            print(f"  {key}: {len(value)} tests")
    
    print("\n=== Checking Quality Gates ===\n")
    
    # Check all gates
    all_passed, messages = checker.check_all(metrics)
    
    for message in messages:
        if "FAILED" in message:
            print(f"❌ {message}")
        else:
            print(f"✅ {message}")
    
    print()
    if all_passed:
        print("✅ All quality gates passed. Proceeding with rollout.")
        return 0
    else:
        print("❌ Quality gates failed. Blocking rollout.")
        return 1


if __name__ == "__main__":
    exit(main())
