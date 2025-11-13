"""Tool calling example with validation."""

import os
from dotenv import load_dotenv
from src.llm_client import LLMClient
from src.tools import (
    tool_execution_wrapper,
    GetUserInfoArgs,
    UpdateTicketStatusArgs,
    SendNotificationArgs,
    get_user_info,
    update_ticket_status,
    send_notification
)

load_dotenv()


def main():
    """Run tool calling examples."""
    print("Tool Calling Examples")
    print("=" * 60)
    print()
    
    # Example 1: Get user info
    print("Example 1: Get user info")
    print("-" * 60)
    
    result = tool_execution_wrapper(
        "get_user_info",
        {"user_id": "user123"},
        get_user_info,
        GetUserInfoArgs
    )
    
    print(f"Success: {result['success']}")
    if result['success']:
        print(f"Result: {result['result']}")
    else:
        print(f"Error: {result['error']}")
    print()
    
    # Example 2: Update ticket status
    print("Example 2: Update ticket status")
    print("-" * 60)
    
    result = tool_execution_wrapper(
        "update_ticket_status",
        {"ticket_id": "TICKET-12345", "status": "resolved"},
        update_ticket_status,
        UpdateTicketStatusArgs
    )
    
    print(f"Success: {result['success']}")
    if result['success']:
        print(f"Result: {result['result']}")
    else:
        print(f"Error: {result['error']}")
    print()
    
    # Example 3: Invalid ticket ID (should fail validation)
    print("Example 3: Invalid ticket ID (validation failure)")
    print("-" * 60)
    
    result = tool_execution_wrapper(
        "update_ticket_status",
        {"ticket_id": "INVALID-123", "status": "resolved"},
        update_ticket_status,
        UpdateTicketStatusArgs
    )
    
    print(f"Success: {result['success']}")
    if result['success']:
        print(f"Result: {result['result']}")
    else:
        print(f"Error: {result['error']}")
    print()
    
    # Example 4: Send notification
    print("Example 4: Send notification")
    print("-" * 60)
    
    result = tool_execution_wrapper(
        "send_notification",
        {
            "user_id": "user123",
            "message": "Your ticket has been resolved!",
            "priority": "high"
        },
        send_notification,
        SendNotificationArgs
    )
    
    print(f"Success: {result['success']}")
    if result['success']:
        print(f"Result: {result['result']}")
    else:
        print(f"Error: {result['error']}")


if __name__ == "__main__":
    main()

