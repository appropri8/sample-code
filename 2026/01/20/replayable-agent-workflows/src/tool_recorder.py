"""Tool recording and replay."""
import json
from pathlib import Path
from typing import Any, Dict, Callable


class ToolRecorder:
    """Record tool calls for replay."""
    
    def __init__(self, run_id: str, recordings_dir: str = "recordings"):
        self.run_id = run_id
        self.recordings_dir = Path(recordings_dir)
        self.recordings_dir.mkdir(parents=True, exist_ok=True)
        self.recordings = []
    
    def record(self, tool_name: str, args: Dict[str, Any], result: Dict[str, Any]):
        """Record a tool call."""
        self.recordings.append({
            "tool_name": tool_name,
            "args": args,
            "result": result
        })
    
    def save(self):
        """Save recordings to file."""
        recording_file = self.recordings_dir / f"{self.run_id}.json"
        with open(recording_file, 'w') as f:
            json.dump(self.recordings, f, indent=2)
    
    def wrap_tool(self, tool_func: Callable) -> Callable:
        """Wrap a tool function to record calls."""
        def wrapped(*args, **kwargs):
            result = tool_func(*args, **kwargs)
            self.record(
                tool_func.__name__,
                {"args": args, "kwargs": kwargs},
                result
            )
            return result
        return wrapped


class ToolReplayer:
    """Replay recorded tool calls."""
    
    def __init__(self, run_id: str, recordings_dir: str = "recordings"):
        self.run_id = run_id
        self.recordings_dir = Path(recordings_dir)
        self.index = 0
        self.recordings = self._load_recordings()
    
    def _load_recordings(self):
        """Load recordings from file."""
        recording_file = self.recordings_dir / f"{self.run_id}.json"
        if not recording_file.exists():
            return []
        
        with open(recording_file, 'r') as f:
            return json.load(f)
    
    def replay(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Replay a recorded tool call."""
        if self.index >= len(self.recordings):
            raise ValueError(f"No more recordings (index={self.index})")
        
        recording = self.recordings[self.index]
        self.index += 1
        
        # Verify tool name matches
        if recording["tool_name"] != tool_name:
            raise ValueError(
                f"Tool mismatch: expected {recording['tool_name']}, "
                f"got {tool_name}"
            )
        
        # Verify args match (optional, can be relaxed)
        # if recording["args"] != args:
        #     print(f"Warning: args mismatch for {tool_name}")
        
        return recording["result"]
    
    def wrap_tool(self, tool_func: Callable) -> Callable:
        """Wrap a tool function to replay from recordings."""
        def wrapped(*args, **kwargs):
            return self.replay(
                tool_func.__name__,
                {"args": args, "kwargs": kwargs}
            )
        return wrapped


def record_tool(recorder: ToolRecorder):
    """Decorator to record tool calls."""
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            recorder.record(
                func.__name__,
                {"args": args, "kwargs": kwargs},
                result
            )
            return result
        return wrapper
    return decorator
