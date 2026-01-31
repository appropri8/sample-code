"""Regression tests from production runs."""
import pytest
import sys
sys.path.insert(0, '.')

from src.agent import Agent, replay_run
from src.checkpoint_store import CheckpointStore
from src.tool_recorder import ToolReplayer


# Mock tools for testing
def search_docs(query: str) -> dict:
    return {"docs": [{"id": "doc1", "content": "test"}], "count": 1}


def generate_answer(query: str, docs: list) -> dict:
    if not docs:
        return {"answer": "No documents found"}
    return {"answer": "Based on the documents..."}


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


def test_agent_completes_successfully(checkpoint_store, tools):
    """Test that agent completes successfully."""
    agent = Agent(tools=tools, checkpoint_store=checkpoint_store)
    result = agent.run("What's our refund policy?")
    
    assert result["steps"] > 0
    assert "answer" in result
    assert result["answer"] != ""


def test_agent_tool_sequence(checkpoint_store, tools):
    """Test that agent follows expected tool sequence."""
    agent = Agent(tools=tools, checkpoint_store=checkpoint_store)
    result = agent.run("What's our refund policy?")
    
    # Load events
    events = checkpoint_store.load_events(result["run_id"])
    
    # Assert tool sequence
    tool_sequence = [e.tool_name for e in events]
    assert "search_docs" in tool_sequence
    assert "generate_answer" in tool_sequence


def test_agent_intermediate_state(checkpoint_store, tools):
    """Test that agent reaches expected intermediate states."""
    agent = Agent(tools=tools, checkpoint_store=checkpoint_store)
    result = agent.run("What's our refund policy?")
    
    # Load events
    events = checkpoint_store.load_events(result["run_id"])
    
    # Check that docs are retrieved
    search_event = next(e for e in events if e.tool_name == "search_docs")
    assert "docs" in search_event.output_state
    assert len(search_event.output_state["docs"]) > 0


def test_empty_docs_handling(checkpoint_store):
    """Test that agent handles empty docs correctly."""
    # Tools that return empty results
    empty_tools = {
        "search_docs": lambda query: {"docs": [], "count": 0},
        "generate_answer": lambda query, docs: {
            "answer": "No documents found" if not docs else "Based on docs..."
        }
    }
    
    agent = Agent(tools=empty_tools, checkpoint_store=checkpoint_store)
    result = agent.run("What's our refund policy?")
    
    # Should not loop indefinitely
    assert result["steps"] <= 10
    
    # Should have an answer (even if it's "no docs")
    assert "answer" in result


def test_replay_matches_original(checkpoint_store, tools):
    """Test that replay produces same tool sequence as original."""
    # Run agent
    agent = Agent(tools=tools, checkpoint_store=checkpoint_store)
    result = agent.run("What's our refund policy?")
    
    # Get original events
    original_events = checkpoint_store.load_events(result["run_id"])
    
    # Replay
    replayed_events = replay_run(result["run_id"], checkpoint_store)
    
    # Assert same tool sequence
    original_tools = [e.tool_name for e in original_events]
    replayed_tools = [e.tool_name for e in replayed_events]
    assert original_tools == replayed_tools
