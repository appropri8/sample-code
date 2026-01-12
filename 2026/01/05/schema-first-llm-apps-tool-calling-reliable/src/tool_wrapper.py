"""Safe tool execution with validation and error handling."""

import logging
from typing import Callable, Dict, Any, Optional, Type
from pydantic import BaseModel, ValidationError

from .schemas import (
    GetUserInfoArgs,
    UpdateTicketArgs,
    SendNotificationArgs,
)

logger = logging.getLogger(__name__)


# Allowlist of allowed tools and their argument validators
ALLOWED_TOOLS: Dict[str, Type[BaseModel]] = {
    "get_user_info": GetUserInfoArgs,
    "update_ticket": UpdateTicketArgs,
    "send_notification": SendNotificationArgs,
}


def tool_execution_wrapper(
    tool_name: str,
    arguments: dict,
    tool_function: Callable,
    validator: Optional[Type[BaseModel]] = None
) -> dict:
    """Wrapper that validates arguments before calling tool function.
    
    Args:
        tool_name: Name of the tool (must be in ALLOWED_TOOLS)
        arguments: Arguments to pass to tool function
        tool_function: Function to execute
        validator: Optional Pydantic model to validate arguments
                  (if not provided, uses ALLOWED_TOOLS[tool_name])
        
    Returns:
        Dict with:
        - 'success': bool
        - 'result': result if success
        - 'error': error message if failure
    """
    # Check allowlist
    if tool_name not in ALLOWED_TOOLS:
        logger.error(f"Tool {tool_name} not in allowlist")
        return {
            "success": False,
            "error": f"Tool '{tool_name}' is not allowed. Allowed tools: {list(ALLOWED_TOOLS.keys())}"
        }
    
    # Use validator from allowlist if not provided
    if validator is None:
        validator = ALLOWED_TOOLS[tool_name]
    
    logger.info(f"Tool call: {tool_name} with args: {arguments}")
    
    try:
        # Validate arguments
        validated_args = validator(**arguments)
        # Convert to dict for function call
        args_dict = validated_args.model_dump()
        
        # Execute tool
        result = tool_function(**args_dict)
        
        # Log result
        logger.info(f"Tool {tool_name} succeeded: {result}")
        
        return {
            "success": True,
            "result": result
        }
        
    except ValidationError as e:
        logger.error(f"Tool {tool_name} validation failed: {e}")
        # Format validation errors
        errors = []
        for error in e.errors():
            path = " -> ".join(str(x) for x in error["loc"])
            errors.append(f"{path}: {error['msg']}")
        return {
            "success": False,
            "error": f"Invalid arguments: {'; '.join(errors)}"
        }
    
    except PermissionError as e:
        logger.error(f"Tool {tool_name} permission denied: {e}")
        return {
            "success": False,
            "error": f"Permission denied: {str(e)}"
        }
    
    except Exception as e:
        logger.error(f"Tool {tool_name} execution failed: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"Execution failed: {str(e)}"
        }


# Example tool functions
def get_user_info(user_id: str) -> dict:
    """Get user information by user ID.
    
    Args:
        user_id: User identifier (must start with 'user_')
        
    Returns:
        Dict with user information
    """
    # In production, this would query a database
    logger.info(f"Getting user info for {user_id}")
    return {
        "user_id": user_id,
        "name": "John Doe",
        "email": "john@example.com",
        "created_at": "2026-01-05T10:00:00Z"
    }


def update_ticket(ticket_id: str, status: str) -> dict:
    """Update the status of a support ticket.
    
    Args:
        ticket_id: Ticket identifier (must start with 'TICKET-')
        status: New status (open, in_progress, resolved, closed)
        
    Returns:
        Dict with updated ticket information
    """
    # In production, this would update a database
    logger.info(f"Updating ticket {ticket_id} to status {status}")
    return {
        "ticket_id": ticket_id,
        "status": status,
        "updated_at": "2026-01-05T10:00:00Z"
    }


def send_notification(user_id: str, message: str, priority: str = "medium") -> dict:
    """Send a notification to a user.
    
    Args:
        user_id: User identifier
        message: Notification message (max 500 chars)
        priority: Notification priority (low, medium, high)
        
    Returns:
        Dict with notification information
    """
    # In production, this would send via email/SMS/etc
    logger.info(f"Sending {priority} notification to {user_id}: {message[:50]}...")
    return {
        "user_id": user_id,
        "message": message,
        "priority": priority,
        "sent_at": "2026-01-05T10:00:00Z"
    }
