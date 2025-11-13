"""Example of token and cost budgets"""

from src.budgets import TokenBudget, CostBudget, TokenBudgetExceeded, CostBudgetExceeded


def example_token_budget():
    """Example of token budget"""
    budget = TokenBudget(max_tokens=100)
    
    print("Token budget example:")
    
    texts = [
        "This is a short text.",
        "This is a longer text that will use more tokens.",
        "This is an even longer text that might exceed the budget if we keep adding more and more content."
    ]
    
    for i, text in enumerate(texts):
        tokens = budget.count_tokens(text)
        print(f"Text {i+1}: {tokens} tokens")
        
        if budget.check(text):
            budget.add_tokens(tokens)
            print(f"  Added. Remaining: {budget.remaining()} tokens")
        else:
            print(f"  Would exceed budget! Remaining: {budget.remaining()} tokens")
            try:
                budget.add_tokens(tokens)
            except TokenBudgetExceeded as e:
                print(f"  Error: {e}")


def example_cost_budget():
    """Example of cost budget"""
    budget = CostBudget(max_cost_dollars=1.0)
    
    print("\nCost budget example:")
    
    # Simulate LLM calls
    calls = [
        ("gpt-4", 1000, 500),  # $0.03 + $0.03 = $0.06
        ("gpt-4", 2000, 1000),  # $0.06 + $0.06 = $0.12
        ("gpt-4", 5000, 2000),  # $0.15 + $0.12 = $0.27
        ("gpt-4", 10000, 5000),  # $0.30 + $0.30 = $0.60
    ]
    
    for model, input_tokens, output_tokens in calls:
        try:
            budget.add_cost(model, input_tokens, output_tokens)
            print(f"Call: {model}, Cost: ${budget.cost_used:.2f}, Remaining: ${budget.remaining():.2f}")
        except CostBudgetExceeded as e:
            print(f"Error: {e}")
            break


if __name__ == "__main__":
    example_token_budget()
    example_cost_budget()

