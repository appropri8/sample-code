# Open Policy Agent (OPA) policy example for Agent Gateway.
# - Deny tools not on allowlist
# - Deny requests containing forbidden fields
# - Require approval for "write" actions
#
# Usage: evaluate with input like:
#   input := {
#     "agent_id": "agent_001",
#     "role": "action_agent",
#     "tool": "delete_file",
#     "arguments": {"path": "/tmp/foo"}
#   }

package tool_gateway

import future.keywords.if
import future.keywords.in

# Role allowlist: role -> set of tools
role_allowlist := {
  "read_only_agent": {"read_file", "search"},
  "action_agent": {"read_file", "search", "write_file", "delete_file"},
}

# Forbidden keys in request arguments (deny if present)
forbidden_fields := {"password", "api_key", "token", "secret"}

# Tools that require human approval before execution
approval_required := {"write_file", "delete_file"}

# Default deny: allow only if explicitly in allowlist
default allow := false
allow if {
  input.tool in role_allowlist[input.role]
}

# Deny if any forbidden field appears in arguments (recursive check simplified here)
deny_forbidden_fields if {
  some key in input.arguments
  key == forbidden_fields[_]
}

# Deny if tool not in allowlist for role
deny_tool_not_allowed if {
  not input.tool in role_allowlist[input.role]
}

# Require approval for write actions
requires_approval if {
  input.tool == approval_required[_]
}

# Final decision: allow only if allow and not deny_forbidden_fields
decision := "allow" if {
  allow
  not deny_forbidden_fields
} else := "deny"
