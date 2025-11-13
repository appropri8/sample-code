"""Router pattern for schema-first LLM apps."""

from .llm_client import LLMClient
from .schemas import RouterOutput, TicketRouter


class Router:
    """Routes requests to appropriate handlers."""
    
    def __init__(self, llm_client: LLMClient):
        """Initialize router with LLM client."""
        self.llm_client = llm_client
    
    def route(self, user_message: str) -> RouterOutput:
        """Route user request to appropriate handler.
        
        Args:
            user_message: User's message or request
            
        Returns:
            RouterOutput with route, confidence, and reasoning
        """
        prompt = (
            f"Route this user request to the appropriate team. "
            f"Return valid JSON matching the schema.\n\n{user_message}"
        )
        return self.llm_client.call_with_schema(
            prompt,
            RouterOutput,
            system_prompt=(
                "You are a routing assistant. Analyze the user's request and "
                "determine which team should handle it."
            )
        )
    
    def route_ticket(self, ticket_content: str) -> TicketRouter:
        """Route support ticket to appropriate team.
        
        Args:
            ticket_content: Support ticket content
            
        Returns:
            TicketRouter with route, priority, and tags
        """
        prompt = (
            f"Classify and route this support ticket. "
            f"Return valid JSON matching the schema.\n\n{ticket_content}"
        )
        return self.llm_client.call_with_schema(
            prompt,
            TicketRouter,
            system_prompt=(
                "You are a ticket routing assistant. Analyze support tickets and "
                "route them to the appropriate team with appropriate priority."
            )
        )

