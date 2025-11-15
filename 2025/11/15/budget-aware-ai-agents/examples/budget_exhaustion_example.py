"""Example showing budget exhaustion handling."""

from src.budgets import RunBudget
from src.research_agent import ResearchAgent


def main():
    # Create a very small budget to trigger exhaustion
    budget = RunBudget(
        max_steps=2,
        max_tokens=100,
        max_seconds=5,
        max_nested_tool_calls=1
    )
    
    # Create agent with budget
    agent = ResearchAgent(budget)
    
    # Ask a question that will exhaust the budget
    query = "What is machine learning and how does it work?"
    result = agent.answer(query)
    
    print("=" * 60)
    print("Query (with small budget):", query)
    print("=" * 60)
    print("\nAnswer:")
    print(result["answer"])
    print("\n" + "-" * 60)
    print("Budget Status:")
    print(f"  Budget exhausted: {result['budget_exhausted']}")
    print(f"  Steps used: {result['budget_used']['steps']}")
    print(f"  Tokens used: {result['budget_used']['tokens']}")
    print(f"  Time used: {result['budget_used']['seconds']:.2f} seconds")
    print("\nBudget Remaining:")
    remaining = result['budget_remaining']
    print(f"  Steps: {remaining['steps']}")
    print(f"  Tokens: {remaining['tokens']}")
    print(f"  Seconds: {remaining['seconds']:.2f}")


if __name__ == "__main__":
    main()

