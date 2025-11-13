"""Orchestrator example showing end-to-end flow."""

import os
from dotenv import load_dotenv
from src.orchestrator import Orchestrator

load_dotenv()


def main():
    """Run orchestrator examples."""
    orchestrator = Orchestrator()
    
    # Example requests
    requests = [
        {
            "message": "I need help with my billing issue. My payment was declined.",
            "user_id": "user123"
        },
        {
            "message": "The app crashes when I try to upload a file. This is blocking my work.",
            "user_id": "user456"
        },
        {
            "message": "I'm interested in your enterprise plan. Can you send me pricing?",
            "user_id": "user789"
        }
    ]
    
    print("Orchestrator Examples")
    print("=" * 60)
    print()
    
    for i, request in enumerate(requests, 1):
        print(f"Example {i}: {request['message']}")
        print("-" * 60)
        
        result = orchestrator.process_request(
            request['message'],
            request['user_id']
        )
        
        print(f"Success: {result['success']}")
        print(f"Route: {result['route']}")
        if 'confidence' in result:
            print(f"Confidence: {result['confidence']:.2f}")
        print(f"Result: {result['result']}")
        print()


if __name__ == "__main__":
    main()

