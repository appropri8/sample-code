"""Example: Progressive rollout with automatic rollback."""

import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rollout_controller import RolloutController, RolloutThresholds, RolloutStage
from src.agent_factory import create_agent


def main():
    """Run progressive rollout example."""
    print("=== Progressive Rollout Example ===\n")
    
    # Create rollout controller
    controller = RolloutController(
        agent_name="support-agent",
        current_version="v1.3.2",
        candidate_version="v1.3.3",
        thresholds=RolloutThresholds()
    )
    
    print(f"Starting rollout: {controller.current_version} → {controller.candidate_version}")
    print(f"Initial stage: {controller.stage.value}\n")
    
    # Simulate requests from different users
    users = [f"user_{i}" for i in range(100)]
    test_requests = [
        "Search for user john@example.com",
        "Send an email notification",
        "Find information about order #12345"
    ]
    
    for i, user_id in enumerate(users):
        # Determine which version to use
        use_candidate = controller.should_use_candidate(user_id)
        version = controller.candidate_version if use_candidate else controller.current_version
        
        # Process request
        agent = create_agent("support-agent", version)
        request = test_requests[i % len(test_requests)]
        response = agent.process(request)
        
        # Record metrics
        controller.record_metrics(
            version=version,
            error=response.get("error", False),
            latency_ms=response.get("latency_ms", 0),
            cost=response.get("cost", 0),
            policy_violations=response.get("policy_violations", 0)
        )
        
        if i % 20 == 0:
            print(f"Processed {i} requests")
            print(f"  Stage: {controller.stage.value}")
            print(f"  Traffic to candidate: {controller._get_stage_percentage()}%")
    
    # Evaluate and potentially advance
    print("\n=== Evaluating rollout ===")
    advanced = controller.evaluate_and_advance()
    
    if advanced:
        print(f"Advanced to stage: {controller.stage.value}")
    elif controller.stage == RolloutStage.ROLLED_BACK:
        print("Rolled back due to threshold violations")
    else:
        print(f"Staying in stage: {controller.stage.value}")
    
    print("\n=== Rollout complete ===")


if __name__ == "__main__":
    main()
