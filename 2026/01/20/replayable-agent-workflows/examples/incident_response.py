"""Incident response workflow example."""
import sys
sys.path.insert(0, '.')

from src.agent import Agent, replay_run
from src.checkpoint_store import CheckpointStore
from src.time_travel import fork_run, compare_runs


# Mock tools that simulate the incident
def search_docs_broken(query: str) -> dict:
    """Broken tool that returns empty results."""
    return {"docs": [], "count": 0}


def search_docs_fixed(query: str) -> dict:
    """Fixed tool that handles empty results."""
    return {"docs": [], "count": 0}


def generate_answer(query: str, docs: list) -> dict:
    """Answer generation that doesn't handle empty docs."""
    # Old version: doesn't check for empty docs
    return {"answer": f"Based on {len(docs)} documents..."}


def generate_answer_fixed(query: str, docs: list) -> dict:
    """Fixed version that handles empty docs."""
    if not docs:
        return {"answer": "I don't have any documents to answer this question. Please check with support."}
    return {"answer": f"Based on {len(docs)} documents..."}


def main():
    checkpoint_store = CheckpointStore()
    
    # Step 1: Simulate the incident (agent with broken tools)
    print("=" * 60)
    print("STEP 1: Simulating incident (agent gets stuck in loop)")
    print("=" * 60)
    print()
    
    broken_tools = {
        "search_docs": search_docs_broken,
        "generate_answer": generate_answer
    }
    
    agent = Agent(tools=broken_tools, checkpoint_store=checkpoint_store)
    result = agent.run("What's our refund policy?", max_steps=5)
    
    incident_run_id = result['run_id']
    print(f"Incident run ID: {incident_run_id}")
    print(f"Steps: {result['steps']}")
    print()
    
    # Step 2: Replay to understand the issue
    print("=" * 60)
    print("STEP 2: Replaying to understand the issue")
    print("=" * 60)
    print()
    
    events = replay_run(incident_run_id, checkpoint_store)
    
    # Analyze: count how many times search_docs was called
    search_count = sum(1 for e in events if e.tool_name == "search_docs")
    print(f"Analysis: search_docs called {search_count} times")
    print("Issue: Agent keeps searching but gets empty results")
    print()
    
    # Step 3: Fork with fix
    print("=" * 60)
    print("STEP 3: Forking with fix (use fixed generate_answer)")
    print("=" * 60)
    print()
    
    fixed_tools = {
        "search_docs": search_docs_fixed,
        "generate_answer": generate_answer_fixed
    }
    
    fork_id, fork_result = fork_run(
        incident_run_id,
        "step_1",
        {},  # No state modifications, just different tool behavior
        checkpoint_store,
        fixed_tools
    )
    
    print(f"Fork ID: {fork_id}")
    print(f"Steps: {fork_result['steps']}")
    print(f"Answer: {fork_result['answer']}")
    print()
    
    # Step 4: Compare
    print("=" * 60)
    print("STEP 4: Comparing original vs fork")
    print("=" * 60)
    print()
    
    comparison = compare_runs(incident_run_id, fork_id, checkpoint_store)
    print(f"Diverged: {comparison['diverged']}")
    if comparison['diverged']:
        print(f"Divergence point: step {comparison['divergence_point']}")
    print()
    
    # Step 5: Conclusion
    print("=" * 60)
    print("STEP 5: Conclusion")
    print("=" * 60)
    print()
    print("Root cause: generate_answer doesn't handle empty docs")
    print("Fix: Add empty docs check in generate_answer")
    print("Next steps:")
    print("  1. Add regression test for this scenario")
    print("  2. Deploy fixed generate_answer")
    print("  3. Monitor for similar issues")


if __name__ == "__main__":
    main()
