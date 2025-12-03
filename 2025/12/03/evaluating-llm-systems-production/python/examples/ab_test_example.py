"""
Example: A/B testing and shadow testing.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.experiments import ABTest, ShadowTest


def baseline_model(query: str) -> str:
    """Baseline model."""
    return f"Baseline response to: {query}"


def candidate_model(query: str) -> str:
    """Candidate model (improved)."""
    return f"Improved candidate response to: {query}"


def shadow_logger(comparison_data: dict):
    """Logger for shadow test comparisons."""
    print(f"Shadow test comparison logged:")
    print(f"  User: {comparison_data['user_id']}")
    print(f"  Query: {comparison_data['query']}")
    print(f"  Baseline: {comparison_data['baseline_output'][:50]}...")
    print(f"  Candidate: {comparison_data['candidate_output'][:50]}...")
    print()


def main():
    # A/B Test Example
    print("=" * 60)
    print("A/B Test Example")
    print("=" * 60)
    
    ab_test = ABTest(
        experiment_name="prompt_v2",
        baseline_model=baseline_model,
        candidate_model=candidate_model,
        split_ratio=0.5  # 50/50 split
    )
    
    # Simulate requests from different users
    users = ["user_1", "user_2", "user_3", "user_4"]
    queries = [
        "How do I reset my password?",
        "What's the refund policy?",
        "How do I cancel?",
        "Where is my order?"
    ]
    
    for user_id, query in zip(users, queries):
        output, assignment = ab_test.run(user_id, query)
        print(f"User: {user_id}")
        print(f"  Variant: {assignment.variant}")
        print(f"  Cohort: {assignment.cohort}")
        print(f"  Output: {output[:50]}...")
        print()
    
    # Shadow Test Example
    print("=" * 60)
    print("Shadow Test Example")
    print("=" * 60)
    
    shadow_test = ShadowTest(
        experiment_name="new_model_test",
        baseline_model=baseline_model,
        candidate_model=candidate_model,
        logger=shadow_logger
    )
    
    # All users see baseline, candidate runs in background
    for user_id, query in zip(users[:2], queries[:2]):
        baseline_output, comparison = shadow_test.run(user_id, query)
        print(f"User {user_id} sees: {baseline_output[:50]}...")
        print(f"(Candidate also ran in background for comparison)")
        print()


if __name__ == "__main__":
    main()

