"""Example of multi-tenant quota service."""

from src.quota_service import QuotaService
from src.budgets import RunBudget
from src.research_agent import ResearchAgent


def main():
    # Create quota service
    quota_service = QuotaService(default_daily_quota=10000)
    
    # Create a budget for agent runs
    budget = RunBudget(max_steps=10, max_tokens=5000, max_seconds=30)
    
    # Simulate multiple tenants
    tenants = ["tenant_a", "tenant_b", "tenant_c"]
    queries = [
        "What is machine learning?",
        "Explain neural networks",
        "What is deep learning?",
    ]
    
    for tenant_id, query in zip(tenants, queries):
        print("=" * 60)
        print(f"Tenant: {tenant_id}")
        print(f"Query: {query}")
        print("=" * 60)
        
        # Check quota
        estimated_tokens = 2000
        if not quota_service.check_quota(tenant_id, estimated_tokens):
            print(f"Quota exhausted for {tenant_id}")
            print(f"Remaining quota: {quota_service.get_remaining_quota(tenant_id)}")
            print()
            continue
        
        # Run agent
        agent = ResearchAgent(budget)
        result = agent.answer(query)
        
        # Consume quota
        tokens_used = result['budget_used']['tokens']
        quota_service.consume_quota(tenant_id, tokens_used)
        
        print("\nAnswer:")
        print(result["answer"][:150] + "..." if len(result["answer"]) > 150 else result["answer"])
        print(f"\nTokens used: {tokens_used}")
        print(f"Remaining quota: {quota_service.get_remaining_quota(tenant_id)}")
        print()


if __name__ == "__main__":
    main()

