"""Tests for Tracer"""

import json
import tempfile
import os
from src.tracer import Tracer, InMemoryBackend, FileBackend
from src.agent_run import AgentRun


def test_in_memory_backend():
    """Test in-memory backend"""
    backend = InMemoryBackend()
    tracer = Tracer(backend=backend)
    
    run_id = tracer.start_run({"user_input": "test"})
    assert run_id is not None
    assert run_id in backend.runs
    
    tracer.log_step(run_id, {
        "step_id": 1,
        "tool_name": "test_tool",
        "tool_input": {"key": "value"},
        "tool_output": {"result": "ok"}
    })
    
    run = tracer.get_run(run_id)
    assert run is not None
    assert len(run.steps) == 1
    assert run.steps[0].tool_name == "test_tool"
    
    tracer.end_run(run_id, "Final output")
    run = tracer.get_run(run_id)
    assert run.status == "success"
    assert run.final_output == "Final output"


def test_file_backend():
    """Test file backend"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        filepath = f.name
    
    try:
        backend = FileBackend(filepath)
        tracer = Tracer(backend=backend)
        
        run_id = tracer.start_run({"user_input": "test"})
        
        tracer.log_step(run_id, {
            "step_id": 1,
            "tool_name": "test_tool",
            "tool_input": {"key": "value"},
            "tool_output": {"result": "ok"}
        })
        
        tracer.end_run(run_id, "Final output")
        
        # Verify file was written
        assert os.path.exists(filepath)
        
        # Load and verify
        with open(filepath, 'r') as f:
            data = json.load(f)
            assert isinstance(data, list)
            assert len(data) == 1
            assert data[0]["run_id"] == run_id
            assert data[0]["status"] == "success"
            assert len(data[0]["steps"]) == 1
        
        # Create new backend and verify it loads
        backend2 = FileBackend(filepath)
        run = backend2.get_run(run_id)
        assert run is not None
        assert run.status == "success"
        
    finally:
        if os.path.exists(filepath):
            os.unlink(filepath)


def test_error_logging():
    """Test error logging"""
    tracer = Tracer(backend=InMemoryBackend())
    
    run_id = tracer.start_run({"user_input": "test"})
    tracer.log_error(run_id, "Test error")
    
    run = tracer.get_run(run_id)
    assert run.status == "error"
    assert run.error == "Test error"


def test_multiple_steps():
    """Test logging multiple steps"""
    tracer = Tracer(backend=InMemoryBackend())
    
    run_id = tracer.start_run({"user_input": "test"})
    
    for i in range(3):
        tracer.log_step(run_id, {
            "step_id": i + 1,
            "tool_name": f"tool_{i}",
            "tool_input": {"step": i},
            "tool_output": {"result": i}
        })
    
    run = tracer.get_run(run_id)
    assert len(run.steps) == 3
    assert run.steps[0].tool_name == "tool_0"
    assert run.steps[2].tool_name == "tool_2"


def test_get_nonexistent_run():
    """Test getting a run that doesn't exist"""
    tracer = Tracer(backend=InMemoryBackend())
    
    run = tracer.get_run("nonexistent")
    assert run is None


def test_run_id_generation():
    """Test that run IDs are unique"""
    tracer = Tracer(backend=InMemoryBackend())
    
    run_id1 = tracer.start_run({"test": 1})
    run_id2 = tracer.start_run({"test": 2})
    
    assert run_id1 != run_id2
    assert run_id1.startswith("run_")
    assert run_id2.startswith("run_")

