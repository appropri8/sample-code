"""Tool execution with validation and safety checks."""

import logging
from typing import Callable, Dict, Any, Optional, Type
from pydantic import BaseModel, ValidationError, field_validator

logger = logging.getLogger(__name__)


def tool_execution_wrapper(
    tool_name: str,
    arguments: dict,
    tool_function: Callable,
    validator: Optional[Type[BaseModel]] = None
) -> dict:
    """Wrapper that validates arguments before calling tool function.
    
    Args:
        tool_name: Name of the tool
        arguments: Arguments to pass to tool function
        tool_function: Function to execute
        validator: Optional Pydantic model to validate arguments
        
    Returns:
        Dict with 'success' bool and either 'result' or 'error'
    """
    logger.info(f"Tool call: {tool_name} with args: {arguments}")
    
    try:
        # Validate arguments if validator provided
        if validator:
            validated_args = validator(**arguments)
            # Convert to dict for function call
            args_dict = validated_args.model_dump()
        else:
            args_dict = arguments
        
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
        return {
            "success": False,
            "error": f"Invalid arguments: {str(e)}"
        }
    
    except PermissionError as e:
        logger.error(f"Tool {tool_name} permission denied: {e}")
        return {
            "success": False,
            "error": f"Permission denied: {str(e)}"
        }
    
    except Exception as e:
        logger.error(f"Tool {tool_name} execution failed: {e}")
        return {
            "success": False,
            "error": f"Execution failed: {str(e)}"
        }


# Example tool validators
class GetUserInfoArgs(BaseModel):
    """Arguments for get_user_info tool."""
    user_id: str
    
    @field_validator('user_id')
    @classmethod
    def validate_user_id(cls, v):
        if not v or len(v) < 1:
            raise ValueError('user_id must be non-empty')
        return v


class UpdateTicketStatusArgs(BaseModel):
    """Arguments for update_ticket_status tool."""
    ticket_id: str
    status: str
    
    @field_validator('ticket_id')
    @classmethod
    def validate_ticket_id(cls, v):
        if not v.startswith('TICKET-'):
            raise ValueError('ticket_id must start with TICKET-')
        return v


class SendNotificationArgs(BaseModel):
    """Arguments for send_notification tool."""
    user_id: str
    message: str
    priority: str = "medium"
    
    @field_validator('message')
    @classmethod
    def validate_message(cls, v):
        if len(v) > 500:
            raise ValueError('message must be 500 characters or less')
        return v


# Example tool functions
def get_user_info(user_id: str) -> dict:
    """Get user information by user ID."""
    # In production, this would query a database
    return {
        "user_id": user_id,
        "name": "John Doe",
        "email": "john@example.com"
    }


def update_ticket_status(ticket_id: str, status: str) -> dict:
    """Update the status of a support ticket."""
    # In production, this would update a database
    return {
        "ticket_id": ticket_id,
        "status": status,
        "updated_at": "2025-11-13T10:00:00Z"
    }


def send_notification(user_id: str, message: str, priority: str = "medium") -> dict:
    """Send a notification to a user."""
    # In production, this would send via email/SMS/etc
    return {
        "user_id": user_id,
        "message": message,
        "priority": priority,
        "sent_at": "2025-11-13T10:00:00Z"
    }

