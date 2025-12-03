"""
Example: Logging LLM calls.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.logger import LLMLogger
import uuid
import time


def mock_llm_call(query: str) -> str:
    """Mock LLM call for demonstration."""
    time.sleep(0.1)  # Simulate latency
    return f"Response to: {query}"


def main():
    # Initialize logger
    logger = LLMLogger(log_file="llm_logs.jsonl", redact_pii_enabled=True)
    
    # Simulate some LLM calls
    user_id = "user_123"
    queries = [
        "How do I reset my password?",
        "What's the refund policy?",
        "Contact me at john@example.com"
    ]
    
    for query in queries:
        request_id = str(uuid.uuid4())
        
        # Simulate LLM call
        response = mock_llm_call(query)
        
        # Log the call
        log = logger.log_call(
            request_id=request_id,
            user_id=user_id,
            query=query,
            response=response,
            model_name="gpt-4",
            model_version="2024-11-20",
            prompt_version="v1.0",
            latency_ms=100,
            tokens_used=150,
            cost_usd=0.002,
            session_id="session_abc",
            experiment_variant="baseline"
        )
        
        print(f"Logged request: {request_id}")
        print(f"  Query: {query}")
        print(f"  Response: {response[:50]}...")
        print()
    
    # Add feedback
    first_request_id = logger.logs[0].request_id
    logger.add_feedback(
        request_id=first_request_id,
        thumbs_up=True,
        rating=5
    )
    
    print(f"Added feedback for request: {first_request_id}")
    print(f"Total logs: {len(logger.logs)}")


if __name__ == "__main__":
    main()

