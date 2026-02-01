"""Tests for replay module."""
import pytest

from src.replay import replay_and_compare, run_agent_mock


def test_run_agent_mock():
    trace = {"request": "hi", "outcome": "success", "latency_ms": 100, "cost_tokens": 50}
    out = run_agent_mock(trace, "v1")
    assert out["outcome"] == "success"
    assert out["latency_ms"] == 100
    assert out["cost_tokens"] == 50


def test_replay_and_compare_all_pass():
    traces = [
        {"trace_id": "t1", "outcome": "success", "latency_ms": 100, "cost_tokens": 50, "tool_calls": []},
        {"trace_id": "t2", "outcome": "success", "latency_ms": 200, "cost_tokens": 100, "tool_calls": []},
    ]
    summary = replay_and_compare(traces, "v1", "v2", max_latency_ms=5000, max_cost_tokens=1000)
    assert summary["total"] == 2
    assert summary["passed"] == 2
    assert summary["failed"] == 0


def test_replay_and_compare_budget_overrun():
    traces = [
        {"trace_id": "t1", "outcome": "success", "latency_ms": 100, "cost_tokens": 2000, "tool_calls": []},
    ]
    summary = replay_and_compare(traces, "v1", "v2", max_latency_ms=5000, max_cost_tokens=500)
    assert summary["failed"] == 1
    assert summary["budget_overruns"] >= 1


def test_replay_and_compare_tool_misuse():
    traces = [
        {
            "trace_id": "t1",
            "outcome": "success",
            "latency_ms": 100,
            "cost_tokens": 50,
            "tool_calls": [{"name": "disallowed_tool", "args": {}}],
            "allowed_tools": ["search_docs"],
        },
    ]
    summary = replay_and_compare(traces, "v1", "v2", max_latency_ms=5000, max_cost_tokens=1000)
    assert summary["failed"] == 1
    assert summary["tool_misuse"] == 1
