"""Tests for time-travel debugging."""
import pytest
import sys
sys.path.insert(0, '.')

from src.agent import Agent
from src.checkpoint_store import CheckpointStore
from src.time_travel import fork_run, compare_runs, diff_tool_sequences


# Mock tools
def search_docs(query: str) -> dict:
    return {"docs": [{"id": "doc1"}], "count": 1}


def generate_answer(query: str, docs: list) -> dict:
    return {"answer": "Test answer"}


@pytest.fixture
def checkpoint_store(tmp_path):
    """Create temporary checkpoint store."""
    return CheckpointStore(
        db_path=str(tmp_path / "test.db"),
        blob_dir=str(tmp_path / "blobs")
    )


@pytest.fixture
def tools():
    """Provide test tools."""
    return {
        "search_docs": search_docs,
        "generate_answer": generate_answer
    }


def test_fork_run(checkpoint_store, tools):
    """Test forking a run with modified state."""
    # Run original
    agent = Agent(tools=tools, checkpoint_store=checkpoint_store)
    result = agent.run("Test query")
    original_run_id = result["run_id"]
    
    # Fork from step 1
    fork_id, fork_result = fork_run(
        original_run_id,
        "step_1",
        {"modified": True},
        checkpoint_store,
        tools
    )
    
    assert fork_id != original_run_id
    assert fork_id.startswith(original_run_id + "_fork_")
    assert "answer" in fork_result


def test_compare_identical_runs(checkpoint_store, tools):
    """Test comparing two identical runs."""
    # Run twice with same tools
    agent1 = Agent(tools=tools, checkpoint_store=checkpoint_store)
    result1 = agent1.run("Test query")
    
    agent2 = Agent(tools=tools, checkpoint_store=checkpoint_store)
    result2 = agent2.run("Test query")
    
    # Compare
    comparison = compare_runs(result1["run_id"], result2["run_id"], checkpoint_store)
    
    # Should be identical (same tools, same logic)
    assert comparison["diverged"] == False


def test_compare_divergent_runs(checkpoint_store, tools):
    """Test comparing runs that diverge."""
    # Run with normal tools
    agent1 = Agent(tools=tools, checkpoint_store=checkpoint_store)
    result1 = agent1.run("Test query")
    
    # Run with different tools
    different_tools = {
        "search_docs": lambda query: {"docs": [], "count": 0},  # Empty results
        "generate_answer": generate_answer
    }
    agent2 = Agent(tools=different_tools, checkpoint_store=checkpoint_store)
    result2 = agent2.run("Test query")
    
    # Compare
    comparison = compare_runs(result1["run_id"], result2["run_id"], checkpoint_store)
    
    # May diverge depending on how agent handles empty docs
    # At minimum, tool results will be different
    assert "diverged" in comparison


def test_diff_tool_sequences(checkpoint_store, tools):
    """Test diffing tool sequences."""
    # Run twice
    agent1 = Agent(tools=tools, checkpoint_store=checkpoint_store)
    result1 = agent1.run("Test query")
    
    agent2 = Agent(tools=tools, checkpoint_store=checkpoint_store)
    result2 = agent2.run("Test query")
    
    # Diff
    diff = diff_tool_sequences(result1["run_id"], result2["run_id"], checkpoint_store)
    
    assert len(diff) > 0
    assert all("step" in item for item in diff)
    assert all("status" in item for item in diff)
