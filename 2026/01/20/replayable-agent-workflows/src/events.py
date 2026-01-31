"""Event definitions for agent execution."""
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Dict


@dataclass
class StepEvent:
    """Event emitted for each agent step."""
    step_id: str
    run_id: str
    step_number: int
    input_state: Dict[str, Any]
    decision: str
    tool_name: str
    tool_args: Dict[str, Any]
    tool_result: Dict[str, Any]
    output_state: Dict[str, Any]
    timestamp: datetime
    duration_ms: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StepEvent':
        """Create event from dictionary."""
        data = data.copy()
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


@dataclass
class Checkpoint:
    """Checkpoint storing agent state at a specific step."""
    run_id: str
    step_id: str
    step_number: int
    timestamp: datetime
    messages: list
    tool_calls: list
    model_config: Dict[str, Any]
    state: Dict[str, Any]
    agent_version: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert checkpoint to dictionary."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Checkpoint':
        """Create checkpoint from dictionary."""
        data = data.copy()
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)
