"""Example: Safe tool execution with validation."""

from src.tool_wrapper import (
    tool_execution_wrapper,
    get_user_info,
    update_ticket,
    send_notification,
)
from src.schemas import GetUserInfoArgs, UpdateTicketArgs, SendNotificationArgs


def main():
    """Demonstrate safe tool execution."""
    
    print("Example 1: Successful tool execution")
    print("=" * 50)
    result = tool_execution_wrapper(
        "get_user_info",
        {"user_id": "user_123"},
        get_user_info,
        GetUserInfoArgs
    )
    
    if result["success"]:
        print(f"✅ Success: {result['result']}")
    else:
        print(f"❌ Error: {result['error']}")
    print()
    
    print("Example 2: Validation error (invalid user_id format)")
    print("=" * 50)
    result = tool_execution_wrapper(
        "get_user_info",
        {"user_id": "invalid"},  # Doesn't start with 'user_'
        get_user_info,
        GetUserInfoArgs
    )
    
    if result["success"]:
        print(f"✅ Success: {result['result']}")
    else:
        print(f"❌ Error: {result['error']}")
    print()
    
    print("Example 3: Tool not in allowlist")
    print("=" * 50)
    def malicious_tool():
        return "hacked"
    
    result = tool_execution_wrapper(
        "malicious_tool",  # Not in ALLOWED_TOOLS
        {},
        malicious_tool
    )
    
    if result["success"]:
        print(f"✅ Success: {result['result']}")
    else:
        print(f"❌ Error: {result['error']}")
    print()
    
    print("Example 4: Update ticket")
    print("=" * 50)
    result = tool_execution_wrapper(
        "update_ticket",
        {"ticket_id": "TICKET-456", "status": "resolved"},
        update_ticket,
        UpdateTicketArgs
    )
    
    if result["success"]:
        print(f"✅ Success: {result['result']}")
    else:
        print(f"❌ Error: {result['error']}")
    print()
    
    print("Example 5: Send notification")
    print("=" * 50)
    result = tool_execution_wrapper(
        "send_notification",
        {
            "user_id": "user_789",
            "message": "Your ticket has been resolved",
            "priority": "high"
        },
        send_notification,
        SendNotificationArgs
    )
    
    if result["success"]:
        print(f"✅ Success: {result['result']}")
    else:
        print(f"❌ Error: {result['error']}")
    print()
    
    print("Example 6: Message too long (validation error)")
    print("=" * 50)
    long_message = "x" * 501  # Over 500 char limit
    
    result = tool_execution_wrapper(
        "send_notification",
        {
            "user_id": "user_789",
            "message": long_message
        },
        send_notification,
        SendNotificationArgs
    )
    
    if result["success"]:
        print(f"✅ Success: {result['result']}")
    else:
        print(f"❌ Error: {result['error']}")


if __name__ == "__main__":
    main()
