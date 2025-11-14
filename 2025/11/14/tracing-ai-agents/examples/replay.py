"""Replay script for agent traces"""

import json
import sys
from typing import Dict, Any, Optional, List
from src.agent_run import AgentRun


def load_trace(filepath: str, run_id: Optional[str] = None) -> Dict[str, Any]:
    """Load a trace from JSON file"""
    with open(filepath, 'r') as f:
        traces = json.load(f)
        
        # Handle both single dict and list of dicts
        if isinstance(traces, dict):
            traces = [traces]
        
        if run_id:
            trace = next((t for t in traces if t["run_id"] == run_id), None)
            if not trace:
                raise ValueError(f"Run {run_id} not found in {filepath}")
            return trace
        else:
            # Return most recent
            if not traces:
                raise ValueError(f"No traces found in {filepath}")
            return traces[-1]


def load_all_traces(filepath: str) -> List[Dict[str, Any]]:
    """Load all traces from JSON file"""
    with open(filepath, 'r') as f:
        traces = json.load(f)
        if isinstance(traces, dict):
            return [traces]
        return traces


def replay_trace(trace: Dict[str, Any], verbose: bool = True) -> None:
    """Replay a trace and print steps"""
    print(f"\n{'='*60}")
    print(f"Replaying run: {trace['run_id']}")
    print(f"{'='*60}")
    print(f"Status: {trace['status']}")
    print(f"Start time: {trace['start_time']}")
    print(f"End time: {trace.get('end_time', 'N/A')}")
    print(f"\nUser input: {trace['metadata'].get('user_input', 'N/A')}")
    print(f"\nSteps ({len(trace.get('steps', []))}):")
    
    for step in trace.get("steps", []):
        print(f"\n  Step {step['step_id']} ({step['timestamp']}):")
        print(f"    Tool: {step['tool_name']}")
        print(f"    Input: {json.dumps(step['tool_input'], indent=6)}")
        if verbose:
            print(f"    Output: {json.dumps(step['tool_output'], indent=6)}")
    
    print(f"\nFinal output: {trace.get('final_output', 'N/A')}")
    if trace.get('error'):
        print(f"\nError: {trace['error']}")
    print(f"\n{'='*60}")


def replay_dry_run(trace: Dict[str, Any]) -> None:
    """Replay using recorded tool outputs (dry run)"""
    print(f"\nDry run replay for: {trace['run_id']}")
    print(f"Replaying {len(trace.get('steps', []))} steps using recorded outputs...\n")
    
    for step in trace.get("steps", []):
        print(f"Step {step['step_id']}: {step['tool_name']}")
        print(f"  Input: {step['tool_input']}")
        print(f"  Output (recorded): {step['tool_output']}")
        print()


def compare_replay(trace: Dict[str, Any], new_prompt: str) -> Dict[str, Any]:
    """Re-run with new prompt and compare (placeholder)"""
    print(f"\nComparing replay with new prompt...")
    print(f"Original prompt: {trace['metadata'].get('prompt', 'N/A')}")
    print(f"New prompt: {new_prompt}")
    
    # In real implementation, you would:
    # 1. Re-run the agent with new_prompt
    # 2. Compare outputs
    # 3. Return comparison
    
    # For demo, just return a placeholder
    return {
        "original_output": trace.get("final_output"),
        "new_output": "New output would go here (requires actual agent re-run)",
        "differences": ["Would show differences here"]
    }


def list_traces(filepath: str) -> None:
    """List all traces in a file"""
    traces = load_all_traces(filepath)
    
    print(f"\nFound {len(traces)} trace(s) in {filepath}:\n")
    for i, trace in enumerate(traces, 1):
        print(f"{i}. {trace['run_id']}")
        print(f"   Status: {trace.get('status', 'unknown')}")
        print(f"   Steps: {len(trace.get('steps', []))}")
        print(f"   Start: {trace.get('start_time', 'N/A')}")
        print()


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python replay.py <trace_file> [run_id] [--verbose|--quiet]")
        print("  python replay.py <trace_file> --list")
        print("  python replay.py <trace_file> --dry-run [run_id]")
        sys.exit(1)
    
    filepath = sys.argv[1]
    
    if "--list" in sys.argv:
        list_traces(filepath)
        return
    
    verbose = "--quiet" not in sys.argv
    run_id = None
    
    # Find run_id if provided
    for i, arg in enumerate(sys.argv):
        if arg == "--list" or arg == "--verbose" or arg == "--quiet" or arg == "--dry-run":
            continue
        if i > 1 and arg != filepath:
            run_id = arg
            break
    
    try:
        trace = load_trace(filepath, run_id)
        
        if "--dry-run" in sys.argv:
            replay_dry_run(trace)
        else:
            replay_trace(trace, verbose=verbose)
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

