#!/usr/bin/env python3
"""Run policy checks on agent code."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.contracts import POLICY_RULES


def check_policies() -> bool:
    """Check that policies are properly configured."""
    errors = []
    
    # Check max_steps is set
    if POLICY_RULES.get("max_steps") is None:
        errors.append("max_steps policy not set")
    elif POLICY_RULES["max_steps"] > 20:
        errors.append(f"max_steps too high: {POLICY_RULES['max_steps']}")
    
    # Check forbidden tools list exists
    if not POLICY_RULES.get("forbidden_tools_in_test"):
        errors.append("forbidden_tools_in_test policy not set")
    
    # Check required parameters are defined
    if not POLICY_RULES.get("required_parameters"):
        errors.append("required_parameters policy not set")
    
    if errors:
        print("Policy check failed:")
        for error in errors:
            print(f"  - {error}")
        return False
    
    print("Policy checks passed")
    return True


if __name__ == "__main__":
    success = check_policies()
    sys.exit(0 if success else 1)
