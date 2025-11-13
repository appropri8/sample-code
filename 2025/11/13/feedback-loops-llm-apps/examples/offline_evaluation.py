"""Example: Offline evaluation of prompt versions"""

from src.evaluation import (
    evaluate_output_with_llm_judge,
    evaluate_prompt_version,
    compare_prompt_versions,
    load_logged_interactions
)


def example_single_evaluation():
    """Example: Evaluate a single output."""
    input_text = "How do I handle errors in Python?"
    output_text = "Use try-except blocks to handle errors. For example: try: ... except Exception as e: ..."
    
    score = evaluate_output_with_llm_judge(
        input_text=input_text,
        output_text=output_text,
        criteria="clarity and usefulness"
    )
    
    print("Evaluation Result:")
    print(f"  Clarity: {score['clarity']}/10")
    print(f"  Usefulness: {score['usefulness']}/10")
    print(f"  Accuracy: {score['accuracy']}/10")
    print(f"  Overall: {score['overall']}/10")
    print(f"  Reason: {score['reason']}")


def example_version_evaluation():
    """Example: Evaluate a prompt version."""
    # Load logged interactions (from database or file)
    interactions = [
        {
            "input": "How do I handle errors?",
            "output": "Use try-except blocks...",
            "prompt_version": "v1",
            "model": "gpt-4"
        },
        {
            "input": "What is Python?",
            "output": "Python is a programming language...",
            "prompt_version": "v1",
            "model": "gpt-4"
        }
    ]
    
    metrics = evaluate_prompt_version(
        logged_interactions=interactions,
        prompt_version="v1"
    )
    
    print("\nPrompt Version Evaluation:")
    print(f"  Sample size: {metrics.get('sample_size', 0)}")
    print(f"  Avg clarity: {metrics.get('avg_clarity', 0):.2f}")
    print(f"  Avg usefulness: {metrics.get('avg_usefulness', 0):.2f}")
    print(f"  Avg accuracy: {metrics.get('avg_accuracy', 0):.2f}")
    print(f"  Avg overall: {metrics.get('avg_overall', 0):.2f}")


def example_version_comparison():
    """Example: Compare multiple prompt versions."""
    # Load logged interactions
    interactions = [
        {
            "input": "How do I handle errors?",
            "output": "Use try-except blocks...",
            "prompt_version": "v1",
            "model": "gpt-4"
        },
        {
            "input": "What is Python?",
            "output": "Python is a programming language...",
            "prompt_version": "v1",
            "model": "gpt-4"
        },
        {
            "input": "How do I handle errors?",
            "output": "To handle errors in Python, use try-except blocks with specific exception types...",
            "prompt_version": "v2",
            "model": "gpt-4"
        },
        {
            "input": "What is Python?",
            "output": "Python is a high-level programming language known for its simplicity...",
            "prompt_version": "v2",
            "model": "gpt-4"
        }
    ]
    
    comparison = compare_prompt_versions(interactions)
    
    print("\nPrompt Version Comparison:")
    print("=" * 50)
    
    for version, metrics in comparison.items():
        print(f"\n{version}:")
        print(f"  Sample size: {metrics.get('sample_size', 0)}")
        print(f"  Avg clarity: {metrics.get('avg_clarity', 0):.2f}")
        print(f"  Avg usefulness: {metrics.get('avg_usefulness', 0):.2f}")
        print(f"  Avg accuracy: {metrics.get('avg_accuracy', 0):.2f}")
        print(f"  Avg overall: {metrics.get('avg_overall', 0):.2f}")


def example_load_from_database():
    """Example: Load interactions from database and evaluate."""
    # Load from database
    interactions = load_logged_interactions(prompt_version="v1")
    
    if not interactions:
        print("No interactions found in database.")
        return
    
    # Evaluate
    metrics = evaluate_prompt_version(interactions, "v1")
    
    print("\nEvaluation from Database:")
    print(f"  Sample size: {metrics.get('sample_size', 0)}")
    print(f"  Avg overall: {metrics.get('avg_overall', 0):.2f}")


if __name__ == "__main__":
    print("Example: Single output evaluation")
    example_single_evaluation()
    
    print("\n" + "=" * 50)
    print("Example: Version evaluation")
    example_version_evaluation()
    
    print("\n" + "=" * 50)
    print("Example: Version comparison")
    example_version_comparison()
    
    print("\n" + "=" * 50)
    print("Example: Load from database")
    # Uncomment to run (requires database setup)
    # example_load_from_database()

