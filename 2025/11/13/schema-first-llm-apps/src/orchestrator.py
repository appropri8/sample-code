"""Orchestrator for schema-first LLM application flow."""

import logging
from typing import Optional
from fastapi import HTTPException
from pydantic import ValidationError

from .llm_client import LLMClient
from .router import Router
from .extractors import EntityExtractor, Summarizer, ContactExtractor
from .tools import tool_execution_wrapper, GetUserInfoArgs, UpdateTicketStatusArgs, SendNotificationArgs
from .tools import get_user_info, update_ticket_status, send_notification

logger = logging.getLogger(__name__)


class Orchestrator:
    """Orchestrates schema-first LLM application flow."""
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        """Initialize orchestrator."""
        self.llm_client = llm_client or LLMClient()
        self.router = Router(self.llm_client)
        self.entity_extractor = EntityExtractor(self.llm_client)
        self.summarizer = Summarizer(self.llm_client)
        self.contact_extractor = ContactExtractor(self.llm_client)
    
    def process_request(self, user_message: str, user_id: str = "anonymous") -> dict:
        """Process user request through schema-first flow.
        
        Args:
            user_message: User's message
            user_id: User ID for context
            
        Returns:
            Dict with success status and result
        """
        try:
            # Step 1: Route request
            route_result = self.router.route(user_message)
            logger.info(f"Routed to: {route_result.route} (confidence: {route_result.confidence})")
            
            # Step 2: Process based on route
            if route_result.route == "billing":
                result = self._handle_billing(user_message)
            elif route_result.route == "tech_support":
                result = self._handle_tech_support(user_message)
            elif route_result.route == "sales":
                result = self._handle_sales(user_message)
            else:
                result = self._handle_other(user_message)
            
            return {
                "success": True,
                "result": result,
                "route": route_result.route,
                "confidence": route_result.confidence
            }
        
        except ValidationError as e:
            logger.error(f"Validation failed: {e}")
            # Try fallback
            try:
                fallback_result = self._handle_fallback(user_message)
                return {
                    "success": True,
                    "result": fallback_result,
                    "route": "fallback"
                }
            except Exception as fallback_error:
                logger.error(f"Fallback also failed: {fallback_error}")
                raise HTTPException(
                    status_code=500,
                    detail="Request could not be processed. Escalated to human support."
                )
        
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    def _handle_billing(self, message: str) -> dict:
        """Handle billing-related requests."""
        # Extract contact info
        contact = self.contact_extractor.extract_contact(message)
        return {
            "type": "billing",
            "contact": contact.model_dump(),
            "message": "Billing request received"
        }
    
    def _handle_tech_support(self, message: str) -> dict:
        """Handle tech support requests."""
        # Extract entities
        entities = self.entity_extractor.extract_entities(message)
        return {
            "type": "tech_support",
            "entities": entities.model_dump(),
            "message": "Tech support request received"
        }
    
    def _handle_sales(self, message: str) -> dict:
        """Handle sales requests."""
        # Generate summary
        summary = self.summarizer.summarize(message)
        return {
            "type": "sales",
            "summary": summary.model_dump(),
            "message": "Sales request received"
        }
    
    def _handle_other(self, message: str) -> dict:
        """Handle other requests."""
        return {
            "type": "other",
            "message": "Request received and will be reviewed"
        }
    
    def _handle_fallback(self, message: str) -> dict:
        """Fallback handler for when validation fails."""
        return {
            "type": "fallback",
            "message": "Request processed with fallback handler"
        }
    
    def execute_tool_safely(self, tool_name: str, arguments: dict) -> dict:
        """Execute a tool with validated arguments.
        
        Args:
            tool_name: Name of tool to execute
            arguments: Tool arguments
            
        Returns:
            Tool execution result
        """
        tool_map = {
            "get_user_info": (get_user_info, GetUserInfoArgs),
            "update_ticket_status": (update_ticket_status, UpdateTicketStatusArgs),
            "send_notification": (send_notification, SendNotificationArgs)
        }
        
        if tool_name not in tool_map:
            raise ValueError(f"Unknown tool: {tool_name}")
        
        tool_function, validator = tool_map[tool_name]
        return tool_execution_wrapper(tool_name, arguments, tool_function, validator)

