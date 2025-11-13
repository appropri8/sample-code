"""Basic example of using BoundedAgent"""

from src.contracts import AgentContract
from src.bounded_agent import BoundedAgent, SimpleAgentCore


def main():
    # Define contract
    contract = AgentContract(
        name="support_bot",
        allowed_tools=["search_kb", "create_ticket"],
        max_runtime_seconds=30,
        max_steps=10,
        max_tokens=10000,
        max_cost_dollars=0.50,
        required_output="text"
    )
    
    # User context
    user_context = {
        "user_id": "user_123",
        "tenant_id": "tenant_456",
        "role": "user",
        "environment": "production",
        "request_id": "req_789",
        "context": {}
    }
    
    # Create agent core
    agent_core = SimpleAgentCore()
    
    # Create bounded agent
    agent = BoundedAgent(
        agent_core=agent_core,
        contract=contract,
        user_context=user_context
    )
    
    # Run
    result = agent.run("How do I reset my password?")
    
    # Check result
    if result.get("error"):
        print(f"Error: {result['error']}")
        if result.get("partial"):
            print(f"Partial results: {result['results']}")
    else:
        print(f"Response: {result['response']}")
        print(f"Budgets used: {result['budgets']}")


if __name__ == "__main__":
    main()

