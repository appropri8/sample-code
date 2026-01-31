"""Run agent with checkpointing."""
import sys
sys.path.insert(0, '.')

from src.agent import Agent
from src.checkpoint_store import CheckpointStore


# Define mock tools
def search_docs(query: str) -> dict:
    """Mock search tool."""
    print(f"  [Tool] search_docs(query='{query}')")
    return {
        "docs": [
            {"id": "doc1", "content": "Refunds allowed within 60 days"},
            {"id": "doc2", "content": "Contact support for refund requests"}
        ],
        "count": 2
    }


def generate_answer(query: str, docs: list) -> dict:
    """Mock answer generation tool."""
    print(f"  [Tool] generate_answer(query='{query}', docs={len(docs)})")
    return {
        "answer": "Based on our policy, refunds are allowed within 60 days of purchase. Please contact support to request a refund."
    }


def main():
    # Setup
    checkpoint_store = CheckpointStore()
    tools = {
        "search_docs": search_docs,
        "generate_answer": generate_answer
    }
    
    # Run agent
    query = "What's our refund policy?"
    print(f"Running agent with query: '{query}'")
    print()
    
    agent = Agent(tools=tools, checkpoint_store=checkpoint_store)
    result = agent.run(query)
    
    print()
    print(f"Run completed!")
    print(f"  Run ID: {result['run_id']}")
    print(f"  Steps: {result['steps']}")
    print(f"  Answer: {result['answer']}")
    print()
    print(f"To replay: python examples/replay_run.py --run-id {result['run_id']}")


if __name__ == "__main__":
    main()
