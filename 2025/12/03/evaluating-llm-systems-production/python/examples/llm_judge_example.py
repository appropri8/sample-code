"""
Example: Using LLM-as-judge to evaluate outputs.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.llm_judge import LLMJudge


def mock_llm(prompt: str) -> str:
    """
    Mock LLM for demonstration.
    In practice, this would call OpenAI, Anthropic, etc.
    """
    # Simple mock that returns "A" or "B" for pairwise
    if "Which output is better?" in prompt:
        if "improved" in prompt.lower():
            return "B"
        else:
            return "A"
    # For scoring
    elif "Score this output" in prompt:
        if "improved" in prompt.lower():
            return "5"
        else:
            return "3"
    # For labeling
    elif "Categorize this output" in prompt:
        if "improved" in prompt.lower():
            return "correct"
        else:
            return "partially_correct"
    
    return "A"


def main():
    # Initialize LLM judge
    judge = LLMJudge(mock_llm)
    
    # Example inputs
    input_text = "How do I reset my password?"
    output_a = "Baseline response: Go to settings and click reset."
    output_b = "Improved response: To reset your password, navigate to Account Settings > Security > Reset Password. You'll receive an email with a reset link."
    
    # Pairwise comparison
    print("Pairwise Comparison:")
    print(f"  Input: {input_text}")
    print(f"  Output A: {output_a}")
    print(f"  Output B: {output_b}")
    winner = judge.pairwise(input_text, output_a, output_b, "Which is more helpful?")
    print(f"  Winner: {winner}\n")
    
    # Scoring
    print("Scoring:")
    score_a = judge.score(input_text, output_a, "Rate helpfulness", "1-5")
    score_b = judge.score(input_text, output_b, "Rate helpfulness", "1-5")
    print(f"  Output A score: {score_a}/5")
    print(f"  Output B score: {score_b}/5\n")
    
    # Labeling
    print("Labeling:")
    labels_a = judge.label(
        input_text,
        output_a,
        expected_behavior="Provide clear steps",
        label_categories={
            "correctness": ["correct", "partially_correct", "wrong"],
            "helpfulness": ["helpful", "somewhat_helpful", "not_helpful"]
        }
    )
    labels_b = judge.label(
        input_text,
        output_b,
        expected_behavior="Provide clear steps",
        label_categories={
            "correctness": ["correct", "partially_correct", "wrong"],
            "helpfulness": ["helpful", "somewhat_helpful", "not_helpful"]
        }
    )
    print(f"  Output A labels: {labels_a}")
    print(f"  Output B labels: {labels_b}")


if __name__ == "__main__":
    main()

