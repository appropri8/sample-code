"""Basic usage example of budget-aware research agent."""

from src.budgets import RunBudget
from src.research_agent import ResearchAgent


def main():
    # Create a budget for quick answers
    budget = RunBudget(
        max_steps=5,
        max_tokens=2000,
        max_seconds=10,
        max_nested_tool_calls=2
    )
    
    # Create agent with budget
    agent = ResearchAgent(budget)
    
    # Ask a question
    query = "What is machine learning?"
    result = agent.answer(query)
    
    print("=" * 60)
    print("Query:", query)
    print("=" * 60)
    print("\nAnswer:")
    print(result["answer"])
    print("\n" + "-" * 60)
    print("Budget Usage:")
    print(f"  Steps used: {result['budget_used']['steps']}")
    print(f"  Tokens used: {result['budget_used']['tokens']}")
    print(f"  Time used: {result['budget_used']['seconds']:.2f} seconds")
    print("\nBudget Remaining:")
    remaining = result['budget_remaining']
    print(f"  Steps: {remaining['steps']}")
    print(f"  Tokens: {remaining['tokens']}")
    print(f"  Seconds: {remaining['seconds']:.2f}")
    print(f"  Budget exhausted: {result['budget_exhausted']}")


if __name__ == "__main__":
    main()

