"""Time-travel debugging example."""
import sys
import argparse
import json
sys.path.insert(0, '.')

from src.checkpoint_store import CheckpointStore
from src.time_travel import fork_run, compare_runs


# Mock tools
def search_docs(query: str) -> dict:
    return {"docs": [], "count": 0}  # Empty results


def generate_answer(query: str, docs: list) -> dict:
    if not docs:
        return {"answer": "I don't have any documents to answer this question."}
    return {"answer": "Based on the documents..."}


def main():
    parser = argparse.ArgumentParser(description="Time-travel debugging")
    parser.add_argument("--run-id", required=True, help="Run ID to fork from")
    parser.add_argument("--step-id", required=True, help="Step ID to fork from")
    parser.add_argument("--modify", required=True, help="State modifications (JSON)")
    args = parser.parse_args()
    
    # Parse modifications
    modifications = json.loads(args.modify)
    
    # Setup
    checkpoint_store = CheckpointStore()
    tools = {
        "search_docs": search_docs,
        "generate_answer": generate_answer
    }
    
    # Fork
    print(f"Forking run {args.run_id} from {args.step_id}")
    print(f"Modifications: {modifications}")
    print()
    
    fork_id, result = fork_run(
        args.run_id,
        args.step_id,
        modifications,
        checkpoint_store,
        tools
    )
    
    print(f"Fork completed!")
    print(f"  Fork ID: {fork_id}")
    print(f"  Steps: {result['steps']}")
    print(f"  Answer: {result['answer']}")
    print()
    
    # Compare
    print("Comparing original vs fork...")
    comparison = compare_runs(args.run_id, fork_id, checkpoint_store)
    
    if comparison["diverged"]:
        print(f"  Diverged at step {comparison['divergence_point']}")
        print(f"  Original: {comparison['details']['run_1']}")
        print(f"  Fork: {comparison['details']['run_2']}")
    else:
        print("  Runs are identical")


if __name__ == "__main__":
    main()
