"""Tests for tool recorder and replayer."""
import pytest
import tempfile
import shutil
import sys
sys.path.insert(0, '.')

from src.tool_recorder import ToolRecorder, ToolReplayer


@pytest.fixture
def temp_recordings_dir():
    """Create temporary recordings directory."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


def test_record_and_replay(temp_recordings_dir):
    """Test recording and replaying tool calls."""
    run_id = "test_run"
    
    # Record
    recorder = ToolRecorder(run_id, recordings_dir=temp_recordings_dir)
    recorder.record("search_docs", {"query": "test"}, {"docs": ["doc1"]})
    recorder.record("generate_answer", {"query": "test"}, {"answer": "test answer"})
    recorder.save()
    
    # Replay
    replayer = ToolReplayer(run_id, recordings_dir=temp_recordings_dir)
    result1 = replayer.replay("search_docs", {"query": "test"})
    result2 = replayer.replay("generate_answer", {"query": "test"})
    
    assert result1 == {"docs": ["doc1"]}
    assert result2 == {"answer": "test answer"}


def test_replay_tool_mismatch(temp_recordings_dir):
    """Test that replay fails on tool name mismatch."""
    run_id = "test_run"
    
    # Record
    recorder = ToolRecorder(run_id, recordings_dir=temp_recordings_dir)
    recorder.record("search_docs", {"query": "test"}, {"docs": []})
    recorder.save()
    
    # Replay with wrong tool name
    replayer = ToolReplayer(run_id, recordings_dir=temp_recordings_dir)
    with pytest.raises(ValueError, match="Tool mismatch"):
        replayer.replay("wrong_tool", {"query": "test"})


def test_wrap_tool_for_recording(temp_recordings_dir):
    """Test wrapping a tool function for recording."""
    run_id = "test_run"
    recorder = ToolRecorder(run_id, recordings_dir=temp_recordings_dir)
    
    # Define and wrap tool
    def search_docs(query: str) -> dict:
        return {"docs": ["doc1", "doc2"]}
    
    wrapped = recorder.wrap_tool(search_docs)
    
    # Call wrapped tool
    result = wrapped("test query")
    
    assert result == {"docs": ["doc1", "doc2"]}
    assert len(recorder.recordings) == 1
    assert recorder.recordings[0]["tool_name"] == "search_docs"
