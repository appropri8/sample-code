"""
Example: Running evaluation harness on golden set.
"""

import sys
import os
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.eval_harness import EvaluationHarness


def baseline_model(query: str) -> str:
    """Baseline model (simple response)."""
    return f"Baseline response to: {query}"


def candidate_model(query: str) -> str:
    """Candidate model (improved response)."""
    return f"Improved candidate response to: {query}"


def simple_labeler(input_text: str, output: str, expected_behavior: str, variant: str) -> dict:
    """Simple labeler for demonstration."""
    # In practice, this would use LLM-as-judge or human labels
    # For demo, we'll use simple heuristics
    labels = {}
    
    if "improved" in output.lower():
        labels["correctness"] = "correct"
        labels["helpfulness"] = "helpful"
    else:
        labels["correctness"] = "partially_correct"
        labels["helpfulness"] = "somewhat_helpful"
    
    return labels


def create_sample_golden_set():
    """Create a sample golden set for demonstration."""
    golden_set = [
        {
            "id": "example_001",
            "input": {
                "query": "How do I reset my password?"
            },
            "expected_behavior": "Provide clear steps to reset password"
        },
        {
            "id": "example_002",
            "input": {
                "query": "What's the refund policy?"
            },
            "expected_behavior": "Explain refund policy clearly"
        },
        {
            "id": "example_003",
            "input": {
                "query": "How do I cancel my subscription?"
            },
            "expected_behavior": "Provide steps to cancel subscription"
        }
    ]
    
    golden_set_path = "sample_golden_set.json"
    with open(golden_set_path, 'w') as f:
        json.dump(golden_set, f, indent=2)
    
    return golden_set_path


def main():
    # Create sample golden set
    print("Creating sample golden set...")
    golden_set_path = create_sample_golden_set()
    
    # Initialize evaluation harness
    harness = EvaluationHarness(golden_set_path)
    
    # Run evaluation
    print("\nRunning evaluation...")
    results = harness.run_evaluation(
        baseline_model=baseline_model,
        candidate_model=candidate_model,
        labeler=simple_labeler
    )
    
    # Print results
    harness.print_results(results)
    
    # Check for regressions
    print("\nChecking for regressions...")
    passed = harness.check_regressions(results, min_pass_rate=0.95)
    
    if passed:
        print("\n✅ Evaluation passed!")
    else:
        print("\n❌ Evaluation failed - regressions detected")


if __name__ == "__main__":
    main()

