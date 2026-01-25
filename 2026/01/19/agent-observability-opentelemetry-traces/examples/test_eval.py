"""Example: Test eval script with bad run fixture."""

import sys
import os
import json

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.eval_from_traces import load_traces_from_json, evaluate_traces, print_metrics_table


def test_with_bad_run():
    """Test eval script with the bad run fixture."""
    
    fixture_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "fixtures",
        "bad_run_trace.json"
    )
    
    print(f"Loading bad run fixture from {fixture_path}")
    traces = load_traces_from_json(fixture_path)
    
    print(f"Loaded {len(traces)} trace(s)")
    print("\nComputing metrics...")
    metrics = evaluate_traces(traces)
    
    print_metrics_table(metrics)
    
    # Show what makes this a bad run
    print("\n" + "=" * 60)
    print("BAD RUN ANALYSIS")
    print("=" * 60)
    
    run = metrics["runs"][0]
    print(f"Run ID: {run['run_id']}")
    print(f"Completed: {run['completed']} ❌")
    print(f"Tool Errors: {run['tool_errors']} ❌")
    print(f"Wasted Steps (repeated calls): {run['wasted_steps']['repeated_calls']} ❌")
    print(f"Looping Tools: {run['wasted_steps']['looping_tools']} ❌")
    print(f"Total Tool Calls: {run['total_tool_calls']} (high for failed run)")
    
    print("\nThis run shows:")
    print("  - Failed to complete (max iterations reached)")
    print("  - Multiple tool errors")
    print("  - Repeated tool calls (read_file called multiple times)")
    print("  - High tool call count for a failed run")


if __name__ == "__main__":
    test_with_bad_run()
