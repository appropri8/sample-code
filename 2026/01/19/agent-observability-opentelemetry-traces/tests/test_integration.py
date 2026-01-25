"""Integration tests for agent observability."""

import sys
import os
import json

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.agent import run_agent, trace
from src.eval_from_traces import evaluate_traces, load_traces_from_json
from src.redaction import redact_value


def test_agent_run():
    """Test that agent runs generate traces."""
    result = run_agent(
        task="Test task",
        user_id="test-user",
        workspace_id="test-workspace"
    )
    
    assert result is not None
    assert "success" in result
    assert "iterations" in result
    
    # Flush traces
    trace.get_tracer_provider().force_flush()


def test_redaction():
    """Test that redaction works."""
    # Test email redaction
    original = "Contact user@example.com for details"
    redacted = redact_value(original)
    assert "REDACTED_EMAIL" in redacted
    assert "user@example.com" not in redacted
    
    # Test API key redaction
    original = "api_key=sk-1234567890abcdef"
    redacted = redact_value(original)
    assert "REDACTED_SK_KEY" in redacted or "REDACTED_API_KEY" in redacted
    
    # Test password redaction
    original = "password=secret123"
    redacted = redact_value(original)
    assert "REDACTED_PASSWORD" in redacted


def test_eval_with_fixture():
    """Test eval script with bad run fixture."""
    fixture_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "fixtures",
        "bad_run_trace.json"
    )
    
    traces = load_traces_from_json(fixture_path)
    assert len(traces) > 0
    
    metrics = evaluate_traces(traces)
    
    # Check that metrics are computed
    assert "completion_rate" in metrics
    assert "tool_success_rate" in metrics
    assert "runs" in metrics
    assert len(metrics["runs"]) > 0
    
    # Check that bad run is detected
    run = metrics["runs"][0]
    assert run["completed"] == False  # Bad run should not be completed
    assert run["tool_errors"] > 0  # Should have errors
    assert run["wasted_steps"]["repeated_calls"] > 0  # Should have repeated calls


if __name__ == "__main__":
    print("Running integration tests...")
    
    print("\n1. Testing agent run...")
    test_agent_run()
    print("   ✓ Agent run test passed")
    
    print("\n2. Testing redaction...")
    test_redaction()
    print("   ✓ Redaction test passed")
    
    print("\n3. Testing eval with fixture...")
    test_eval_with_fixture()
    print("   ✓ Eval test passed")
    
    print("\n" + "=" * 60)
    print("All integration tests passed!")
    print("=" * 60)
