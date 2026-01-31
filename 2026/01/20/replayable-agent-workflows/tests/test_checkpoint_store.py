"""Tests for checkpoint store."""
import pytest
import tempfile
import shutil
from datetime import datetime
from pathlib import Path
import sys
sys.path.insert(0, '.')

from src.checkpoint_store import CheckpointStore
from src.events import Checkpoint, StepEvent


@pytest.fixture
def temp_store():
    """Create temporary checkpoint store."""
    temp_dir = tempfile.mkdtemp()
    store = CheckpointStore(
        db_path=f"{temp_dir}/test.db",
        blob_dir=f"{temp_dir}/blobs"
    )
    yield store
    shutil.rmtree(temp_dir)


def test_save_and_load_checkpoint(temp_store):
    """Test saving and loading a checkpoint."""
    checkpoint = Checkpoint(
        run_id="test_run",
        step_id="step_1",
        step_number=1,
        timestamp=datetime.now(),
        messages=[{"role": "user", "content": "test"}],
        tool_calls=[{"tool": "search", "args": {}}],
        model_config={"temperature": 0.7},
        state={"query": "test"},
        agent_version="v1.0"
    )
    
    temp_store.save_checkpoint(checkpoint)
    loaded = temp_store.load_checkpoint("test_run", "step_1")
    
    assert loaded is not None
    assert loaded.run_id == "test_run"
    assert loaded.step_id == "step_1"
    assert loaded.step_number == 1
    assert loaded.state == {"query": "test"}


def test_save_and_load_event(temp_store):
    """Test saving and loading an event."""
    event = StepEvent(
        step_id="step_1",
        run_id="test_run",
        step_number=1,
        input_state={"query": "test"},
        decision="tool",
        tool_name="search",
        tool_args={"query": "test"},
        tool_result={"docs": []},
        output_state={"query": "test", "docs": []},
        timestamp=datetime.now(),
        duration_ms=100.0
    )
    
    temp_store.save_event(event)
    events = temp_store.load_events("test_run")
    
    assert len(events) == 1
    assert events[0].step_id == "step_1"
    assert events[0].tool_name == "search"


def test_load_nonexistent_checkpoint(temp_store):
    """Test loading a checkpoint that doesn't exist."""
    loaded = temp_store.load_checkpoint("nonexistent", "step_1")
    assert loaded is None


def test_load_events_for_nonexistent_run(temp_store):
    """Test loading events for a run that doesn't exist."""
    events = temp_store.load_events("nonexistent")
    assert events == []
