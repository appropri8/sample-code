"""Prompt release gate runner.

Loads a candidate prompt and a set of eval cases, sends each case through a
model, grades the response, and writes a Markdown scorecard (report.md).

Run with zero setup (uses a mock model that reproduces a realistic failure),
or point `model_fn` at your own LLM client for live runs.

Usage:
    python run_eval.py --prompt prompts/support_v2.txt --cases eval_cases.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import graders


def mock_model(prompt: str, user_input: str) -> str:
    """Stand-in model that reproduces a realistic bad rollout for support_v2.

    The 'warmer' candidate (support_v2) over-promises refunds, leaks PII, and
    drops the JSON format. The safe production prompt (support_v1) does not.
    This lets you see the gate catch a regression by swapping --prompt.

    Replace this with a real client call, e.g.:
        return openai.chat.completions.create(model=..., messages=[...]).choices[0].message.content
    """
    warmer = "warm and human" in prompt.lower()

    if "50 days" in user_input.lower():
        if warmer:
            return "Of course! I'll get that full refund started for your 50-day-old order right away."
        return "Our full-refund window is 30 days, so for a 50-day order I can offer store credit or an exchange instead."
    if "jane.doe@example.com" in user_input:
        if warmer:
            return "Sure jane.doe@example.com, I can see your email jane.doe@example.com on file. Here is everything I have."
        return "I can help with your late order, but I won't read back your email or other personal details. What's your order number?"
    if user_input.strip().lower().startswith("return my open orders as json"):
        if warmer:
            return "Here are your orders: order 102 has status shipped, order 118 is pending."
        return '[{"order_id": 102, "status": "shipped"}, {"order_id": 118, "status": "pending"}]'
    if "ignore your" in user_input.lower() or "maintenance override" in user_input.lower():
        return "Refusing. I follow the real refund policy and won't reveal customer data."
    return "Thanks for reaching out! How can I help you with your order today?"


def load_prompt(path: str) -> str:
    return Path(path).read_text(encoding="utf-8").strip()


def load_cases(path: str) -> list[dict]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def run(prompt: str, cases: list[dict], model_fn=mock_model) -> dict:
    results = []
    passed = 0
    failed = 0
    for case in cases:
        response = model_fn(prompt, case["input"])
        ok, note = graders.grade(case, response)
        if ok:
            passed += 1
        else:
            failed += 1
        results.append({"id": case["id"], "passed": ok, "note": note, "response": response})
    return {"passed": passed, "failed": failed, "results": results}


def write_report(candidate: str, summary: dict, out: str = "report.md") -> None:
    lines = [f"# Prompt Release Gate Report", ""]
    lines.append(f"**Prompt candidate:** `{candidate}`")
    lines.append("")
    lines.append(f"- Passed: **{summary['passed']}**")
    lines.append(f"- Failed: **{summary['failed']}**")
    lines.append("")
    failures = [r for r in summary["results"] if not r["passed"]]
    if failures:
        lines.append("## Failures")
        lines.append("")
        for r in failures:
            lines.append(f"- `{r['id']}`: {r['note']}")
        lines.append("")
        lines.append("**Release decision: BLOCKED**")
    else:
        lines.append("**Release decision: PASS**")
    lines.append("")
    Path(out).write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Run a prompt release gate.")
    ap.add_argument("--prompt", default="prompts/support_v2.txt")
    ap.add_argument("--cases", default="eval_cases.json")
    ap.add_argument("--out", default="report.md")
    args = ap.parse_args()

    prompt = load_prompt(args.prompt)
    cases = load_cases(args.cases)
    summary = run(prompt, cases)

    print(f"Prompt candidate: {Path(args.prompt).name}\n")
    print(f"Passed: {summary['passed']}")
    print(f"Failed: {summary['failed']}\n")
    for r in summary["results"]:
        if not r["passed"]:
            print(f"- {r['id']}: {r['note']}")
    decision = "BLOCKED" if summary["failed"] else "PASS"
    print(f"\nRelease decision: {decision}")

    write_report(Path(args.prompt).name, summary, args.out)
    # A blocked prompt must fail the build in CI.
    return 1 if decision == "BLOCKED" else 0


if __name__ == "__main__":
    sys.exit(main())
