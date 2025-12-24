# Example Rego policies for Open Policy Agent (OPA)
# This file shows how policies would look in Rego format
# For production use, deploy OPA and use these policies

package agent_mesh.policies

import rego.v1

# Default deny
default allow = false

# Allow ReadOrders if tenant matches and user has support_role
allow if {
    input.action.tool_name == "ReadOrders"
    input.action.operation == "read"
    input.subject.tenant_id == input.resource.tenant_id
    "support_role" in input.subject.roles
}

# Allow ReadOrders if tenant matches and user has admin_role
allow if {
    input.action.tool_name == "ReadOrders"
    input.action.operation == "read"
    input.subject.tenant_id == input.resource.tenant_id
    "admin_role" in input.subject.roles
}

# Allow IssueRefund if user has finance_role
allow if {
    input.action.tool_name == "IssueRefund"
    input.action.operation == "write"
    "finance_role" in input.subject.roles
}

# Allow ExportCSV if user has admin_role
allow if {
    input.action.tool_name == "ExportCSV"
    input.action.operation == "read"
    "admin_role" in input.subject.roles
}

# Constraints for ExportCSV: row limit
constraints.row_limit = 1000 if {
    input.action.tool_name == "ExportCSV"
    allow
}

# Constraints for ReadOrders: mask email field for support users
constraints.field_masking = ["email"] if {
    input.action.tool_name == "ReadOrders"
    allow
    "support_role" in input.subject.roles
    not "admin_role" in input.subject.roles
}

# Deny cross-tenant access
allow = false if {
    input.action.tool_name == "ReadOrders"
    input.subject.tenant_id != input.resource.tenant_id
}

