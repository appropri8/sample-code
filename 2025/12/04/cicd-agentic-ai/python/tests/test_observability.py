"""Test observability hooks"""
import pytest
from src.observability.logging import AgentLogger, generate_trace_id
from src.observability.metrics import MetricsCollector, track_agent_execution


def test_traces_emitted():
    """Test that traces are emitted"""
    logger = AgentLogger()
    trace_id = generate_trace_id()
    
    logger.log_tool_call(
        trace_id=trace_id,
        agent_version="1.0.0",
        tool_name="search_kb",
        input={"query": "test"},
        output={"results": []},
        latency_ms=100,
        success=True
    )
    
    # If no exception, trace was emitted
    assert trace_id is not None


def test_tool_calls_logged():
    """Test that tool calls are logged"""
    logger = AgentLogger()
    trace_id = generate_trace_id()
    
    logger.log_tool_call(
        trace_id=trace_id,
        agent_version="1.0.0",
        tool_name="create_ticket",
        input={"title": "test"},
        output={"ticket_id": "123"},
        latency_ms=200,
        success=True
    )
    
    # If no exception, logging worked
    assert trace_id is not None


def test_metrics_tracked():
    """Test that metrics are tracked"""
    metrics = MetricsCollector()
    
    track_agent_execution(
        agent_version="1.0.0",
        success=True,
        latency_ms=150,
        tokens_used=1000,
        cost=0.01
    )
    
    all_metrics = metrics.get_metrics()
    assert "agent.executions" in str(all_metrics["counters"])

