#!/usr/bin/env python3
"""Run agent against sandbox scenarios."""

import yaml
import json
import sys
from pathlib import Path
from typing import Dict, List, Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agent import create_agent


def load_scenario(path: str) -> Dict[str, Any]:
    """Load a scenario from a YAML file."""
    with open(path, "r") as f:
        return yaml.safe_load(f)


def run_scenario(scenario: Dict[str, Any], agent) -> Dict[str, Any]:
    """Run agent against scenario and return results."""
    result = {
        "scenario": scenario["name"],
        "passed": False,
        "errors": [],
        "tool_calls": [],
        "steps": 0
    }
    
    try:
        user_message = scenario.get("user_message", "")
        max_steps = scenario.get("max_steps", 10)
        
        response = agent.process(user_message, max_steps=max_steps)
        result["tool_calls"] = response.get("tool_calls", [])
        result["steps"] = response.get("step_count", 0)
        
        # Check max steps
        if result["steps"] > scenario.get("max_steps", 10):
            result["errors"].append(
                f"Exceeded max steps: {result['steps']} > {scenario.get('max_steps', 10)}"
            )
        
        # Check expected tools
        expected_tools = {t["name"] for t in scenario.get("expected_tools", [])}
        actual_tools = {tc.get("tool_name", "") for tc in result["tool_calls"]}
        
        if expected_tools and not expected_tools.issubset(actual_tools):
            missing = expected_tools - actual_tools
            result["errors"].append(f"Missing tool calls: {missing}")
        
        # Check for errors in response
        if response.get("errors"):
            result["errors"].extend(response["errors"])
        
        result["passed"] = len(result["errors"]) == 0
        
    except Exception as e:
        result["errors"].append(str(e))
        result["passed"] = False
    
    return result


def main():
    """Run all scenarios and print results."""
    scenario_dir = Path(__file__).parent.parent / "scenarios"
    scenarios = list(scenario_dir.glob("*.yaml"))
    
    if not scenarios:
        print("No scenarios found!")
        sys.exit(1)
    
    agent = create_agent(use_mocks=True)
    results = []
    
    print("Running sandbox scenarios...\n")
    
    for scenario_path in scenarios:
        scenario = load_scenario(str(scenario_path))
        result = run_scenario(scenario, agent)
        results.append(result)
        
        status = "PASS" if result["passed"] else "FAIL"
        print(f"{status}: {result['scenario']}")
        if result["errors"]:
            for error in result["errors"]:
                print(f"  ERROR: {error}")
        print()
    
    # Summary
    passed = sum(1 for r in results if r["passed"])
    total = len(results)
    
    print(f"Results: {passed}/{total} scenarios passed")
    
    # Exit with non-zero if any scenario failed
    failed = [r for r in results if not r["passed"]]
    if failed:
        print(f"\n{len(failed)} scenario(s) failed")
        sys.exit(1)
    else:
        print("\nAll scenarios passed")
        sys.exit(0)


if __name__ == "__main__":
    main()
