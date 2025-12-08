"""Example: Using shadow mode to test a new agent version."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.shadow_mode import ShadowModeRouter


def main():
    """Run shadow mode example."""
    print("=== Shadow Mode Example ===\n")
    
    # Create router with current and candidate versions
    router = ShadowModeRouter(
        agent_name="support-agent",
        current_version="v1.3.2",
        candidate_version="v1.3.3"  # Running in shadow mode
    )
    
    # Process some requests
    test_requests = [
        "Search for user john@example.com",
        "Send an email notification",
        "Find information about order #12345"
    ]
    
    for request in test_requests:
        print(f"\nUser request: {request}")
        response = router.process(request)
        print(f"Response: {response['response']}")
        print(f"Tool calls: {response['tool_calls']}")
        print(f"Cost: ${response['cost']:.2f}")
        print(f"Latency: {response['latency_ms']:.2f}ms")
    
    print("\n=== Shadow mode complete ===")
    print("Check logs for comparisons between v1.3.2 and v1.3.3")


if __name__ == "__main__":
    main()
