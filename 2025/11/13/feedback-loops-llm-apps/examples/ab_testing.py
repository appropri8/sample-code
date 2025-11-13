"""Example: A/B testing setup"""

from src.ab_testing import get_or_assign_variant, log_ab_test
from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def example_ab_test():
    """Example: Run A/B test between two prompt versions."""
    
    # Define variants (80% v1, 20% v2)
    variants = {"v1": 0.8, "v2": 0.2}
    test_name = "prompt_version_test"
    
    # Simulate user request
    user_id = "user_123"
    input_text = "How do I handle errors in Python?"
    
    # Get or assign variant
    variant = get_or_assign_variant(
        test_name=test_name,
        user_id=user_id,
        variants=variants
    )
    
    print(f"User {user_id} assigned to variant: {variant}")
    
    # Get prompt for variant
    prompt = get_prompt(variant)
    
    # Call LLM
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": input_text}
        ]
    )
    
    output = response.choices[0].message.content
    
    # Prepare result
    result = {
        "input": input_text,
        "output": output,
        "model": "gpt-4",
        "tokens": {
            "input": response.usage.prompt_tokens,
            "output": response.usage.completion_tokens
        },
        "latency_ms": 0,  # Would be measured in real app
        "cost_estimate": estimate_cost(
            response.usage.prompt_tokens,
            response.usage.completion_tokens,
            "gpt-4"
        )
    }
    
    # Log A/B test
    request_id = f"req_{int(__import__('time').time() * 1000)}"
    log_ab_test(
        request_id=request_id,
        user_id=user_id,
        test_name=test_name,
        variant=variant,
        result=result
    )
    
    return result


def get_prompt(version: str) -> str:
    """Get prompt by version."""
    prompts = {
        "v1": "You are a helpful assistant. Answer questions clearly and concisely.",
        "v2": "You are a helpful assistant. Always provide detailed explanations with examples."
    }
    return prompts.get(version, prompts["v1"])


def estimate_cost(prompt_tokens: int, completion_tokens: int, model: str) -> float:
    """Estimate cost."""
    pricing = {
        "gpt-4": {"prompt": 0.03, "completion": 0.06},
        "gpt-4-turbo": {"prompt": 0.01, "completion": 0.03},
        "gpt-3.5-turbo": {"prompt": 0.0015, "completion": 0.002}
    }
    
    if model not in pricing:
        model = "gpt-4"
    
    return (
        (prompt_tokens / 1000) * pricing[model]["prompt"] +
        (completion_tokens / 1000) * pricing[model]["completion"]
    )


def analyze_ab_test_results():
    """Example: Analyze A/B test results."""
    from src.ab_testing import get_ab_test_results
    from datetime import datetime, timedelta
    
    test_name = "prompt_version_test"
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=7)  # Last 7 days
    
    results = get_ab_test_results(
        test_name=test_name,
        start_date=start_date,
        end_date=end_date
    )
    
    print("\nA/B Test Results:")
    print("=" * 50)
    
    for variant, metrics in results.items():
        print(f"\n{variant}:")
        print(f"  Sample size: {metrics.get('sample_size', 0)}")
        print(f"  Task success rate: {metrics.get('task_success_rate', 0):.2%}")
        print(f"  Human help rate: {metrics.get('human_help_rate', 0):.2%}")
        print(f"  Cost per success: ${metrics.get('cost_per_success', 0):.4f}")
        
        latency = metrics.get('latency_percentiles', {})
        if latency:
            print(f"  P95 latency: {latency.get('p95', 0):.0f}ms")


if __name__ == "__main__":
    print("Running A/B test example...")
    result = example_ab_test()
    print(f"\nResult: {result['output'][:100]}...")
    
    print("\nAnalyzing results...")
    analyze_ab_test_results()

