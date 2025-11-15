"""Example of deep research with larger budget."""

from src.budgets import RunBudget
from src.research_agent import ResearchAgent


def main():
    # Create a budget for deep research
    budget = RunBudget(
        max_steps=20,
        max_tokens=50000,
        max_seconds=60,
        max_nested_tool_calls=10
    )
    
    # Create agent with budget
    agent = ResearchAgent(budget)
    
    # Ask a complex question
    query = "Explain the differences between supervised and unsupervised learning, including use cases and examples"
    result = agent.answer(query)
    
    print("=" * 60)
    print("Deep Research Query:", query)
    print("=" * 60)
    print("\nAnswer:")
    print(result["answer"])
    print("\n" + "-" * 60)
    print("Documents Found:", result["documents_found"])
    print("\nBudget Usage:")
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

