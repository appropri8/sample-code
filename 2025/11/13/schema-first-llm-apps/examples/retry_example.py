"""Example showing retry logic for invalid JSON."""

import os
from dotenv import load_dotenv
from src.llm_client import LLMClient
from src.schemas import TicketRouter

load_dotenv()


def main():
    """Run retry example."""
    client = LLMClient()
    
    print("Retry Example")
    print("=" * 60)
    print()
    print("This example demonstrates automatic retry when JSON validation fails.")
    print("The LLM client will retry up to 3 times with error feedback.")
    print()
    
    ticket_content = """
    User: My payment failed and I need a refund immediately. 
    This is urgent and I'm very frustrated. The transaction ID is TXN-12345.
    """
    
    print(f"Ticket content: {ticket_content.strip()}")
    print("-" * 60)
    print()
    
    try:
        result = client.call_with_schema(
            f"Route this ticket: {ticket_content}",
            TicketRouter,
            max_retries=3
        )
        
        print("Successfully routed ticket:")
        print(f"  Route: {result.route}")
        print(f"  Priority: {result.priority}")
        print(f"  Requires escalation: {result.requires_escalation}")
        print(f"  Tags: {result.tags}")
        if result.estimated_resolution_time:
            print(f"  Estimated resolution: {result.estimated_resolution_time} minutes")
        
    except ValueError as e:
        print(f"Failed after retries: {e}")
        print("This would typically escalate to human review or use a fallback.")


if __name__ == "__main__":
    main()

