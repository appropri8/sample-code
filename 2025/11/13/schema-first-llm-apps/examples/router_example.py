"""Router example using schema-first approach."""

import os
from dotenv import load_dotenv
from src.router import Router
from src.llm_client import LLMClient

load_dotenv()


def main():
    """Run router examples."""
    client = LLMClient()
    router = Router(client)
    
    # Example requests
    requests = [
        "I need help with my billing issue. My payment was declined.",
        "The app crashes when I try to upload a file. This is blocking my work.",
        "I'm interested in your enterprise plan. Can you send me pricing?",
        "Just wanted to say thanks for the great service!"
    ]
    
    print("Router Examples")
    print("=" * 60)
    print()
    
    for i, request in enumerate(requests, 1):
        print(f"Example {i}: {request}")
        print("-" * 60)
        
        result = router.route(request)
        
        print(f"Route: {result.route}")
        print(f"Confidence: {result.confidence:.2f}")
        print(f"Reasoning: {result.reasoning}")
        print()


if __name__ == "__main__":
    main()

