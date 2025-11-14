"""Tests for AgentRun and AgentStep"""

from src.agent_run import AgentRun, AgentStep
from datetime import datetime


def test_agent_step():
    """Test AgentStep creation"""
    step = AgentStep(
        step_id=1,
        timestamp="2025-11-14T10:00:00Z",
        tool_name="test_tool",
        tool_input={"key": "value"},
        tool_output={"result": "ok"}
    )
    
    assert step.step_id == 1
    assert step.tool_name == "test_tool"
    assert step.tool_input == {"key": "value"}
    assert step.tool_output == {"result": "ok"}


def test_agent_run():
    """Test AgentRun creation"""
    run = AgentRun(
        run_id="test_run",
        metadata={"user_input": "test"}
    )
    
    assert run.run_id == "test_run"
    assert run.status == "running"
    assert len(run.steps) == 0
    assert run.final_output is None


def test_agent_run_to_dict():
    """Test AgentRun serialization"""
    run = AgentRun(
        run_id="test_run",
        metadata={"user_input": "test"}
    )
    
    step = AgentStep(
        step_id=1,
        timestamp="2025-11-14T10:00:00Z",
        tool_name="test_tool",
        tool_input={"key": "value"},
        tool_output={"result": "ok"}
    )
    
    run.steps.append(step)
    run.final_output = "Final"
    run.status = "success"
    
    data = run.to_dict()
    
    assert data["run_id"] == "test_run"
    assert data["status"] == "success"
    assert data["final_output"] == "Final"
    assert len(data["steps"]) == 1
    assert data["steps"][0]["tool_name"] == "test_tool"


def test_agent_run_from_dict():
    """Test AgentRun deserialization"""
    data = {
        "run_id": "test_run",
        "metadata": {"user_input": "test"},
        "steps": [
            {
                "step_id": 1,
                "timestamp": "2025-11-14T10:00:00Z",
                "tool_name": "test_tool",
                "tool_input": {"key": "value"},
                "tool_output": {"result": "ok"}
            }
        ],
        "final_output": "Final",
        "status": "success",
        "start_time": "2025-11-14T10:00:00Z",
        "end_time": "2025-11-14T10:00:05Z"
    }
    
    run = AgentRun.from_dict(data)
    
    assert run.run_id == "test_run"
    assert run.status == "success"
    assert run.final_output == "Final"
    assert len(run.steps) == 1
    assert run.steps[0].tool_name == "test_tool"


def test_agent_run_with_multiple_steps():
    """Test AgentRun with multiple steps"""
    run = AgentRun(
        run_id="test_run",
        metadata={"user_input": "test"}
    )
    
    for i in range(3):
        step = AgentStep(
            step_id=i + 1,
            timestamp="2025-11-14T10:00:00Z",
            tool_name=f"tool_{i}",
            tool_input={"step": i},
            tool_output={"result": i}
        )
        run.steps.append(step)
    
    assert len(run.steps) == 3
    assert run.steps[0].tool_name == "tool_0"
    assert run.steps[2].tool_name == "tool_2"

