"""Evaluate traces and compute metrics."""

import json
from typing import List, Dict, Any, Optional
from collections import defaultdict


class TraceSpan:
    """Simple span representation for evaluation."""
    
    def __init__(self, data: Dict[str, Any]):
        self.name = data.get("name", "")
        self.attributes = data.get("attributes", {})
        self.events = data.get("events", [])
        self.start_time = data.get("start_time", 0)
        self.end_time = data.get("end_time", 0)
        self.duration_ms = (self.end_time - self.start_time) / 1_000_000 if self.end_time > self.start_time else 0


class Trace:
    """Simple trace representation for evaluation."""
    
    def __init__(self, data: Dict[str, Any]):
        self.trace_id = data.get("trace_id", "")
        self.spans = [TraceSpan(span) for span in data.get("spans", [])]
    
    def find_root_span(self) -> Optional[TraceSpan]:
        """Find the root span (agent.run)."""
        for span in self.spans:
            if span.name == "agent.run":
                return span
        return self.spans[0] if self.spans else None


def load_traces_from_json(filepath: str) -> List[Trace]:
    """Load traces from JSON file."""
    with open(filepath, "r") as f:
        data = json.load(f)
    
    # Handle different JSON formats
    if isinstance(data, list):
        return [Trace(trace) for trace in data]
    elif "traces" in data:
        return [Trace(trace) for trace in data["traces"]]
    else:
        return [Trace(data)]


def compute_tool_success_rate(traces: List[Trace]) -> Dict[str, Dict[str, Any]]:
    """Compute success rate per tool from traces."""
    tool_stats = defaultdict(lambda: {"success": 0, "error": 0})
    
    for trace in traces:
        for span in trace.spans:
            if span.name == "tool.call":
                tool_name = span.attributes.get("tool.name", "unknown")
                status = span.attributes.get("tool.status", "unknown")
                
                if status == "success":
                    tool_stats[tool_name]["success"] += 1
                elif status == "error":
                    tool_stats[tool_name]["error"] += 1
    
    # Compute rates
    rates = {}
    for tool, stats in tool_stats.items():
        total = stats["success"] + stats["error"]
        rates[tool] = {
            "success_rate": stats["success"] / total if total > 0 else 0,
            "total_calls": total,
            "success_count": stats["success"],
            "error_count": stats["error"],
        }
    
    return rates


def compute_completion_rate(traces: List[Trace]) -> Dict[str, Any]:
    """Compute how many runs completed successfully."""
    completed = 0
    failed = 0
    
    for trace in traces:
        root_span = trace.find_root_span()
        if root_span:
            if root_span.attributes.get("agent.completed") == True:
                completed += 1
            else:
                failed += 1
    
    total = completed + failed
    return {
        "completion_rate": completed / total if total > 0 else 0,
        "completed": completed,
        "failed": failed,
        "total": total,
    }


def detect_wasted_steps(trace: Trace) -> Dict[str, Any]:
    """Detect loops and repeated tool calls."""
    tool_calls = []
    for span in trace.spans:
        if span.name == "tool.call":
            tool_name = span.attributes.get("tool.name", "unknown")
            tool_args = str(span.attributes.get("tool.args", ""))
            tool_calls.append((tool_name, tool_args))
    
    # Detect repeated identical calls
    seen = set()
    repeats = []
    for i, (tool, args) in enumerate(tool_calls):
        key = (tool, args)
        if key in seen:
            repeats.append(i)
        seen.add(key)
    
    # Detect loops (same tool called 3+ times)
    tool_counts = defaultdict(int)
    for tool, _ in tool_calls:
        tool_counts[tool] += 1
    
    loops = [tool for tool, count in tool_counts.items() if count >= 3]
    
    return {
        "repeated_calls": len(repeats),
        "looping_tools": loops,
        "total_tool_calls": len(tool_calls),
        "unique_tool_calls": len(set(tool_calls)),
    }


def compute_time_to_first_output(trace: Trace) -> Optional[float]:
    """Time from start to first useful tool result (in milliseconds)."""
    root_span = trace.find_root_span()
    if not root_span:
        return None
    
    start_time = root_span.start_time
    
    # Find first successful tool call
    for span in trace.spans:
        if span.name == "tool.call":
            if span.attributes.get("tool.status") == "success":
                first_output_time = span.start_time
                return (first_output_time - start_time) / 1_000_000  # Convert to ms
    
    return None


def compute_cost_per_run(trace: Trace) -> float:
    """Compute total cost for a run."""
    total_cost = 0.0
    
    for span in trace.spans:
        if span.name == "llm.call":
            cost = span.attributes.get("llm.cost_estimate", 0.0)
            if isinstance(cost, (int, float)):
                total_cost += float(cost)
    
    return total_cost


def compute_total_tool_calls(trace: Trace) -> int:
    """Count total tool calls in a trace."""
    return sum(1 for span in trace.spans if span.name == "tool.call")


def compute_tool_errors(trace: Trace) -> int:
    """Count tool errors in a trace."""
    return sum(
        1 for span in trace.spans
        if span.name == "tool.call" and span.attributes.get("tool.status") == "error"
    )


def evaluate_traces(traces: List[Trace]) -> Dict[str, Any]:
    """Evaluate traces and compute metrics."""
    metrics = {
        "tool_success_rate": compute_tool_success_rate(traces),
        "completion_rate": compute_completion_rate(traces),
        "runs": [],
    }
    
    for trace in traces:
        root_span = trace.find_root_span()
        if not root_span:
            continue
        
        run_metrics = {
            "run_id": trace.trace_id[:16],  # Truncate for readability
            "completed": root_span.attributes.get("agent.completed", False),
            "cost": compute_cost_per_run(trace),
            "time_to_first_output_ms": compute_time_to_first_output(trace),
            "wasted_steps": detect_wasted_steps(trace),
            "total_tool_calls": compute_total_tool_calls(trace),
            "tool_errors": compute_tool_errors(trace),
            "task": root_span.attributes.get("agent.task", "unknown")[:50],
        }
        metrics["runs"].append(run_metrics)
    
    return metrics


def print_metrics_table(metrics: Dict[str, Any]):
    """Print metrics as a table."""
    print("\n" + "=" * 100)
    print("EVALUATION METRICS")
    print("=" * 100)
    
    # Completion rate
    completion = metrics["completion_rate"]
    print(f"\nOverall Completion Rate: {completion['completion_rate']:.2%}")
    print(f"  Completed: {completion['completed']}")
    print(f"  Failed: {completion['failed']}")
    print(f"  Total: {completion['total']}")
    
    # Tool success rates
    print("\nTool Success Rates:")
    for tool, stats in metrics["tool_success_rate"].items():
        print(f"  {tool}: {stats['success_rate']:.2%} ({stats['success_count']}/{stats['total_calls']})")
    
    # Run details
    print("\nRun Details:")
    print(f"{'Run ID':<12} {'Completed':<10} {'Cost ($)':<10} {'Tool Calls':<12} {'Errors':<8} {'Time to Output (ms)':<20} {'Wasted Steps':<15}")
    print("-" * 100)
    
    for run in metrics["runs"]:
        completed = "Yes" if run["completed"] else "No"
        cost = f"${run['cost']:.4f}"
        tool_calls = run["total_tool_calls"]
        errors = run["tool_errors"]
        time_to_output = f"{run['time_to_first_output_ms']:.0f}" if run['time_to_first_output_ms'] else "N/A"
        wasted = run["wasted_steps"]["repeated_calls"]
        
        print(f"{run['run_id']:<12} {completed:<10} {cost:<10} {tool_calls:<12} {errors:<8} {time_to_output:<20} {wasted:<15}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python eval_from_traces.py <traces.json>")
        sys.exit(1)
    
    filepath = sys.argv[1]
    
    print(f"Loading traces from {filepath}...")
    traces = load_traces_from_json(filepath)
    print(f"Loaded {len(traces)} traces")
    
    print("Computing metrics...")
    metrics = evaluate_traces(traces)
    
    print_metrics_table(metrics)
    
    # Also output JSON for programmatic use
    output_file = filepath.replace(".json", "_metrics.json")
    with open(output_file, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"\nMetrics saved to {output_file}")
