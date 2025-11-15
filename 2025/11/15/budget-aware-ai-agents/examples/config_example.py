"""Example using configuration file for budgets."""

from src.config_loader import load_budget_config
from src.research_agent import ResearchAgent


def main():
    # Load budgets from config file
    try:
        budgets = load_budget_config("budgets.yaml")
    except FileNotFoundError:
        print("budgets.yaml not found. Using default budgets.")
        from src.budgets import RunBudget
        budgets = {
            "quick_answer": RunBudget(max_steps=5, max_tokens=2000, max_seconds=10),
            "deep_research": RunBudget(max_steps=20, max_tokens=50000, max_seconds=60),
        }
    
    # Use different budgets for different queries
    queries = [
        ("What is Python?", "quick_answer"),
        ("Explain the architecture of distributed systems", "deep_research"),
    ]
    
    for query, budget_name in queries:
        print("=" * 60)
        print(f"Query: {query}")
        print(f"Budget: {budget_name}")
        print("=" * 60)
        
        budget = budgets[budget_name]
        agent = ResearchAgent(budget)
        result = agent.answer(query)
        
        print("\nAnswer:")
        print(result["answer"][:200] + "..." if len(result["answer"]) > 200 else result["answer"])
        print("\nBudget Usage:")
        print(f"  Steps: {result['budget_used']['steps']}")
        print(f"  Tokens: {result['budget_used']['tokens']}")
        print(f"  Time: {result['budget_used']['seconds']:.2f}s")
        print()


if __name__ == "__main__":
    main()

