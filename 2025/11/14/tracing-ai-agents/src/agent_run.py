"""Agent run representation"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime


@dataclass
class AgentStep:
    """Represents one step in an agent run"""
    step_id: int
    timestamp: str
    tool_name: str
    tool_input: Dict[str, Any]
    tool_output: Dict[str, Any]
    messages_at_step: List[Dict[str, str]] = field(default_factory=list)


@dataclass
class AgentRun:
    """Represents one complete agent run"""
    run_id: str
    metadata: Dict[str, Any]
    steps: List[AgentStep] = field(default_factory=list)
    final_output: Optional[str] = None
    status: str = "running"  # running, success, error, timeout
    error: Optional[str] = None
    start_time: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    end_time: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "run_id": self.run_id,
            "metadata": self.metadata,
            "steps": [
                {
                    "step_id": s.step_id,
                    "timestamp": s.timestamp,
                    "tool_name": s.tool_name,
                    "tool_input": s.tool_input,
                    "tool_output": s.tool_output,
                    "messages_at_step": s.messages_at_step
                }
                for s in self.steps
            ],
            "final_output": self.final_output,
            "status": self.status,
            "error": self.error,
            "start_time": self.start_time,
            "end_time": self.end_time
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentRun":
        """Create AgentRun from dictionary"""
        steps = [
            AgentStep(
                step_id=s["step_id"],
                timestamp=s["timestamp"],
                tool_name=s["tool_name"],
                tool_input=s["tool_input"],
                tool_output=s["tool_output"],
                messages_at_step=s.get("messages_at_step", [])
            )
            for s in data.get("steps", [])
        ]
        
        return cls(
            run_id=data["run_id"],
            metadata=data["metadata"],
            steps=steps,
            final_output=data.get("final_output"),
            status=data.get("status", "success"),
            error=data.get("error"),
            start_time=data.get("start_time", datetime.utcnow().isoformat()),
            end_time=data.get("end_time")
        )

