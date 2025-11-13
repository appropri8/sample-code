"""Example of tool permissions"""

from src.permissions import (
    get_tools_for_role,
    get_tools_for_env,
    can_call_tool,
    get_tools_for_context,
    log_tool_call
)


def example_role_permissions():
    """Example of role-based permissions"""
    print("Role-based permissions:")
    
    roles = ["user", "admin", "readonly"]
    for role in roles:
        tools = get_tools_for_role(role)
        print(f"  {role}: {tools}")


def example_env_permissions():
    """Example of environment-based permissions"""
    print("\nEnvironment-based permissions:")
    
    envs = ["production", "staging", "development"]
    for env in envs:
        tools = get_tools_for_env(env)
        print(f"  {env}: {tools}")


def example_tool_matrix():
    """Example of tool capability matrix"""
    print("\nTool capability matrix:")
    
    tools = ["search_kb", "delete_ticket", "reset_database"]
    roles = ["user", "admin"]
    envs = ["production", "development"]
    
    for tool in tools:
        print(f"\n  {tool}:")
        for role in roles:
            for env in envs:
                can_call = can_call_tool(tool, role, env)
                print(f"    {role} in {env}: {can_call}")


def example_context_permissions():
    """Example of context-based permissions"""
    print("\nContext-based permissions:")
    
    contexts = [
        ("user_1", "tenant_1", "user", "production"),
        ("user_2", "enterprise", "admin", "production"),
        ("user_3", "tenant_2", "user", "development"),
    ]
    
    for user_id, tenant_id, role, env in contexts:
        tools = get_tools_for_context(user_id, tenant_id, role, env)
        print(f"  {user_id} ({role}, {env}): {tools}")


def example_audit_logging():
    """Example of audit logging"""
    print("\nAudit logging:")
    
    user_context = {
        "user_id": "user_123",
        "tenant_id": "tenant_456",
        "role": "admin",
        "environment": "production"
    }
    
    log_tool_call("delete_ticket", {"ticket_id": "ticket_789"}, user_context)


if __name__ == "__main__":
    example_role_permissions()
    example_env_permissions()
    example_tool_matrix()
    example_context_permissions()
    example_audit_logging()

