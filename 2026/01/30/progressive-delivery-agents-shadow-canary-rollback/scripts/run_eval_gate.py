#!/usr/bin/env python3
"""
Run offline eval and exit 0 if pass, 1 if fail. Use in CI as quality gate.
"""
import sys
from pathlib import Path

# Repo root
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root))

from src.trace_loader import load_traces
from src.replay import replay_and_compare

# Thresholds: fail if more than this many traces fail or budget overruns
MAX_FAILED = 0
MAX_BUDGET_OVERRUNS = 0
MAX_TOOL_MISUSE = 0

TRACES_FILE = repo_root / "tests" / "fixtures" / "sample_traces.jsonl"
MAX_LATENCY_MS = 3000
MAX_COST_TOKENS = 1000


def main() -> int:
    if not TRACES_FILE.exists():
        print(f"Eval gate: traces file not found: {TRACES_FILE}", file=sys.stderr)
        return 1

    traces = load_traces(TRACES_FILE)
    summary = replay_and_compare(
        traces,
        "baseline",
        "candidate",
        max_latency_ms=MAX_LATENCY_MS,
        max_cost_tokens=MAX_COST_TOKENS,
    )

    failed = summary["failed"]
    budget = summary["budget_overruns"]
    misuse = summary["tool_misuse"]

    if failed > MAX_FAILED or budget > MAX_BUDGET_OVERRUNS or misuse > MAX_TOOL_MISUSE:
        print(
            f"Quality gate FAILED: failed={failed}, budget_overruns={budget}, tool_misuse={misuse}",
            file=sys.stderr,
        )
        return 1

    print("Quality gate PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
