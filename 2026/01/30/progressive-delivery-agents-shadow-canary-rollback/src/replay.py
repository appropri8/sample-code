"""
Replay traces against baseline and candidate agent versions; compute pass/fail summary.

Usage:
  python -m src.replay --traces tests/fixtures/sample_traces.jsonl \\
    --baseline-version v1 --candidate-version v2 \\
    --max-latency-ms 2000 --max-cost-tokens 800
"""

import argparse
import json
import sys
from pathlib import Path

# Allow running as script from repo root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.trace_loader import load_traces


def run_agent_mock(trace: dict, version: str) -> dict:
    """
    Mock agent run: for demo we use the trace's stored outcome and tool_calls.
    In production you would call the real agent (baseline or candidate) with trace["request"]
    and compare outputs.
    """
    return {
        "outcome": trace.get("outcome", "success"),
        "tool_calls": trace.get("tool_calls", []),
        "latency_ms": trace.get("latency_ms", 0),
        "cost_tokens": trace.get("cost_tokens", 0),
        "response": trace.get("response", ""),
    }


def replay_and_compare(
    traces: list,
    baseline_version: str,
    candidate_version: str,
    max_latency_ms: float,
    max_cost_tokens: float,
) -> dict:
    """
    Replay each trace against baseline and candidate (mock); compute pass/fail.
    Returns summary with: total, passed, failed, tool_misuse, budget_overruns.
    """
    results = {
        "total": len(traces),
        "passed": 0,
        "failed": 0,
        "tool_misuse": 0,
        "budget_overruns": 0,
        "details": [],
    }
    for trace in traces:
        base_out = run_agent_mock(trace, baseline_version)
        cand_out = run_agent_mock(trace, candidate_version)

        passed = True
        reason = []

        # Task success: candidate outcome at least as good as baseline for demo
        if cand_out["outcome"] != "success":
            passed = False
            reason.append("outcome_fail")

        # Tool misuse: candidate used a tool not in allowed set (if present)
        allowed = trace.get("allowed_tools")
        if allowed is not None and cand_out["tool_calls"]:
            for tc in cand_out["tool_calls"]:
                name = tc.get("name") if isinstance(tc, dict) else tc
                if name not in allowed:
                    results["tool_misuse"] += 1
                    passed = False
                    reason.append("tool_misuse")
                    break

        # Budget overruns
        if cand_out["latency_ms"] > max_latency_ms:
            results["budget_overruns"] += 1
            passed = False
            reason.append("latency")
        if cand_out["cost_tokens"] > max_cost_tokens:
            results["budget_overruns"] += 1
            passed = False
            reason.append("cost")

        if passed:
            results["passed"] += 1
        else:
            results["failed"] += 1
        results["details"].append({
            "trace_id": trace.get("trace_id"),
            "passed": passed,
            "reason": reason if not passed else [],
        })
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Replay traces and compare baseline vs candidate.")
    parser.add_argument("--traces", required=True, help="Path to JSONL traces file")
    parser.add_argument("--baseline-version", default="v1", help="Baseline agent version label")
    parser.add_argument("--candidate-version", default="v2", help="Candidate agent version label")
    parser.add_argument("--max-latency-ms", type=float, default=5000, help="Max allowed latency (ms)")
    parser.add_argument("--max-cost-tokens", type=float, default=1000, help="Max allowed cost (tokens)")
    parser.add_argument("--json", action="store_true", help="Output summary as JSON only")
    args = parser.parse_args()

    path = Path(args.traces)
    if not path.exists():
        print(f"Error: traces file not found: {path}", file=sys.stderr)
        return 1

    traces = load_traces(path)
    summary = replay_and_compare(
        traces,
        args.baseline_version,
        args.candidate_version,
        args.max_latency_ms,
        args.max_cost_tokens,
    )

    if args.json:
        print(json.dumps(summary, indent=2))
        return 0 if summary["failed"] == 0 else 1

    print("Replay summary:")
    print(f"  Total:   {summary['total']}")
    print(f"  Passed:  {summary['passed']}")
    print(f"  Failed:  {summary['failed']}")
    print(f"  Tool misuse:  {summary['tool_misuse']}")
    print(f"  Budget overruns: {summary['budget_overruns']}")
    if summary["failed"] > 0:
        print("Failed traces:")
        for d in summary["details"]:
            if not d["passed"]:
                print(f"  - {d['trace_id']}: {d['reason']}")
    return 0 if summary["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
