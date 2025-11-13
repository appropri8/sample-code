"""Basic extraction example using schema-first approach."""

import os
from dotenv import load_dotenv
from src.llm_client import LLMClient
from src.schemas import TicketClassification, ExtractionResult

load_dotenv()


def main():
    """Run basic extraction examples."""
    client = LLMClient()
    
    # Example 1: Classify a ticket
    print("Example 1: Classifying a support ticket")
    print("-" * 50)
    
    ticket_text = "My payment failed and I need a refund immediately. This is urgent!"
    
    classification = client.call_with_schema(
        f"Classify this support ticket: {ticket_text}",
        TicketClassification
    )
    
    print(f"Intent: {classification.intent}")
    print(f"Priority: {classification.priority}")
    print(f"Tags: {classification.tags}")
    print()
    
    # Example 2: Extract contact information
    print("Example 2: Extracting contact information")
    print("-" * 50)
    
    contact_text = "Contact John Smith at john.smith@example.com for more details."
    
    extraction = client.call_with_schema(
        f"Extract name and email from: {contact_text}",
        ExtractionResult
    )
    
    print(f"Name: {extraction.name}")
    print(f"Email: {extraction.email}")
    print(f"Confidence: {extraction.confidence}")
    print()
    
    # Example 3: Extract with missing data
    print("Example 3: Extracting with missing data")
    print("-" * 50)
    
    incomplete_text = "Please contact us for more information."
    
    extraction = client.call_with_schema(
        f"Extract name and email from: {incomplete_text}",
        ExtractionResult
    )
    
    print(f"Name: {extraction.name}")
    print(f"Email: {extraction.email}")
    print(f"Confidence: {extraction.confidence}")


if __name__ == "__main__":
    main()

