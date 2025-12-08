"""Contract validation for agent actions."""

from jsonschema import validate, ValidationError
from typing import Dict, Any, List, Tuple
from .contracts import TOOL_CONTRACT, POLICY_RULES


def validate_agent_action(action: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate an agent action against the contract.
    
    Returns:
        (is_valid, list_of_errors)
    """
    errors = []
    
    # Validate against JSON schema
    try:
        validate(instance=action, schema=TOOL_CONTRACT)
    except ValidationError as e:
        errors.append(f"Schema violation: {e.message}")
        return False, errors
    
    # Check policy rules
    tool_name = action.get("tool_name", "")
    
    # Check forbidden tools in test environment
    if any(forbidden in tool_name for forbidden in POLICY_RULES["forbidden_tools_in_test"]):
        errors.append(f"Forbidden tool in test environment: {tool_name}")
    
    # Check required parameters
    required = POLICY_RULES["required_parameters"].get(tool_name, [])
    params = action.get("parameters", {})
    missing = [p for p in required if p not in params]
    if missing:
        errors.append(f"Missing required parameters for {tool_name}: {missing}")
    
    return len(errors) == 0, errors


def check_policy_violations(actions: List[Dict[str, Any]], environment: str = "test") -> List[str]:
    """
    Check a list of actions for policy violations.
    
    Args:
        actions: List of agent actions
        environment: Environment name (test, staging, prod)
    
    Returns:
        List of policy violation messages
    """
    violations = []
    
    # Check max steps
    if len(actions) > POLICY_RULES["max_steps"]:
        violations.append(
            f"Exceeded max steps: {len(actions)} > {POLICY_RULES['max_steps']}"
        )
    
    # Check for forbidden tools
    if environment == "test":
        for action in actions:
            tool_name = action.get("tool_name", "")
            if any(forbidden in tool_name for forbidden in POLICY_RULES["forbidden_tools_in_test"]):
                violations.append(f"Forbidden tool called in test: {tool_name}")
    
    return violations
