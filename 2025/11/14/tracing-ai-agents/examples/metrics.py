"""Simple metrics aggregation for agent traces"""

import json
import sys
from typing import List, Dict, Any
from collections import defaultdict
from datetime import datetime


def load_all_traces(filepath: str) -> List[Dict[str, Any]]:
    """Load all traces from JSON file"""
    with open(filepath, 'r') as f:
        traces = json.load(f)
        # Handle both single dict and list of dicts
        if isinstance(traces, dict):
            return [traces]
        return traces


def calculate_metrics(traces: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate metrics from traces"""
    if not traces:
        return {}
    
    total_runs = len(traces)
    successful = sum(1 for t in traces if t.get("status") == "success")
    failed = sum(1 for t in traces if t.get("status") == "error")
    running = sum(1 for t in traces if t.get("status") == "running")
    
    total_steps = sum(len(t.get("steps", [])) for t in traces)
    avg_steps = total_steps / total_runs if total_runs > 0 else 0
    
    # Tool usage
    tool_usage = defaultdict(int)
    for trace in traces:
        for step in trace.get("steps", []):
            tool_usage[step.get("tool_name", "unknown")] += 1
    
    # Error types
    error_types = defaultdict(int)
    for trace in traces:
        if trace.get("status") == "error":
            error_msg = trace.get("error", "unknown")
            # Simple error categorization
            error_msg_lower = error_msg.lower()
            if "timeout" in error_msg_lower:
                error_types["timeout"] += 1
            elif "tool" in error_msg_lower:
                error_types["tool_error"] += 1
            elif "rate limit" in error_msg_lower or "rate_limit" in error_msg_lower:
                error_types["rate_limit"] += 1
            else:
                error_types["other"] += 1
    
    # Calculate duration for completed runs
    durations = []
    for trace in traces:
        if trace.get("start_time") and trace.get("end_time"):
            try:
                start = datetime.fromisoformat(trace["start_time"].replace('Z', '+00:00'))
                end = datetime.fromisoformat(trace["end_time"].replace('Z', '+00:00'))
                duration = (end - start).total_seconds()
                durations.append(duration)
            except (ValueError, KeyError):
                pass
    
    avg_duration = sum(durations) / len(durations) if durations else 0
    
    # Steps per tool
    steps_per_tool = defaultdict(list)
    for trace in traces:
        for step in trace.get("steps", []):
            tool_name = step.get("tool_name", "unknown")
            steps_per_tool[tool_name].append(step.get("step_id", 0))
    
    return {
        "total_runs": total_runs,
        "successful_runs": successful,
        "failed_runs": failed,
        "running_runs": running,
        "success_rate": successful / total_runs if total_runs > 0 else 0,
        "failure_rate": failed / total_runs if total_runs > 0 else 0,
        "avg_steps_per_run": avg_steps,
        "avg_duration_seconds": avg_duration,
        "tool_usage": dict(tool_usage),
        "error_types": dict(error_types),
        "steps_per_tool": {k: len(v) for k, v in steps_per_tool.items()}
    }


def print_metrics_report(metrics: Dict[str, Any]) -> None:
    """Print a simple text report"""
    print("\n" + "="*60)
    print("Agent Metrics Report")
    print("="*60)
    
    print(f"\nRun Statistics:")
    print(f"  Total runs: {metrics.get('total_runs', 0)}")
    print(f"  Successful: {metrics.get('successful_runs', 0)}")
    print(f"  Failed: {metrics.get('failed_runs', 0)}")
    print(f"  Running: {metrics.get('running_runs', 0)}")
    print(f"  Success rate: {metrics.get('success_rate', 0):.2%}")
    print(f"  Failure rate: {metrics.get('failure_rate', 0):.2%}")
    
    print(f"\nPerformance:")
    print(f"  Avg steps per run: {metrics.get('avg_steps_per_run', 0):.2f}")
    print(f"  Avg duration: {metrics.get('avg_duration_seconds', 0):.2f} seconds")
    
    print(f"\nTool Usage:")
    tool_usage = metrics.get("tool_usage", {})
    if tool_usage:
        for tool, count in sorted(tool_usage.items(), key=lambda x: x[1], reverse=True):
            print(f"  {tool}: {count} calls")
    else:
        print("  No tool usage data")
    
    print(f"\nError Types:")
    error_types = metrics.get("error_types", {})
    if error_types:
        for error_type, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True):
            print(f"  {error_type}: {count}")
    else:
        print("  No errors")
    
    print("\n" + "="*60)


def success_rate_over_time(traces: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Calculate success rate by day"""
    by_day = {}
    for trace in traces:
        start_time = trace.get("start_time", "")
        if not start_time:
            continue
        
        try:
            # Extract date (YYYY-MM-DD)
            day = start_time[:10]
            if day not in by_day:
                by_day[day] = {"success": 0, "total": 0}
            
            by_day[day]["total"] += 1
            if trace.get("status") == "success":
                by_day[day]["success"] += 1
        except (ValueError, IndexError):
            continue
    
    return [
        {
            "date": day,
            "success_rate": data["success"] / data["total"] if data["total"] > 0 else 0,
            "total": data["total"]
        }
        for day, data in sorted(by_day.items())
    ]


def print_time_series(time_series: List[Dict[str, Any]]) -> None:
    """Print time series data"""
    if not time_series:
        print("\nNo time series data available")
        return
    
    print("\n" + "="*60)
    print("Success Rate Over Time")
    print("="*60)
    print(f"\n{'Date':<12} {'Success Rate':<15} {'Total Runs':<12}")
    print("-" * 60)
    
    for entry in time_series:
        print(f"{entry['date']:<12} {entry['success_rate']:>13.2%} {entry['total']:>11}")


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python metrics.py <trace_file> [--time-series]")
        sys.exit(1)
    
    filepath = sys.argv[1]
    show_time_series = "--time-series" in sys.argv
    
    try:
        traces = load_all_traces(filepath)
        
        if not traces:
            print(f"No traces found in {filepath}")
            sys.exit(1)
        
        metrics = calculate_metrics(traces)
        print_metrics_report(metrics)
        
        if show_time_series:
            time_series = success_rate_over_time(traces)
            print_time_series(time_series)
            
    except FileNotFoundError:
        print(f"Error: File {filepath} not found", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {filepath}: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

