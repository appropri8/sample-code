"""Tracer for agent runs"""

import json
import time
from typing import Dict, Any, Optional
from datetime import datetime
from .agent_run import AgentRun, AgentStep


class InMemoryBackend:
    """In-memory backend for testing"""
    
    def __init__(self):
        self.runs: Dict[str, AgentRun] = {}
    
    def start_run(self, run: AgentRun) -> None:
        self.runs[run.run_id] = run
    
    def log_step(self, run_id: str, step: AgentStep) -> None:
        if run_id in self.runs:
            self.runs[run_id].steps.append(step)
    
    def log_error(self, run_id: str, error: str) -> None:
        if run_id in self.runs:
            self.runs[run_id].status = "error"
            self.runs[run_id].error = error
            self.runs[run_id].end_time = datetime.utcnow().isoformat()
    
    def end_run(self, run_id: str, final_output: str) -> None:
        if run_id in self.runs:
            self.runs[run_id].final_output = final_output
            self.runs[run_id].status = "success"
            self.runs[run_id].end_time = datetime.utcnow().isoformat()
    
    def get_run(self, run_id: str) -> Optional[AgentRun]:
        return self.runs.get(run_id)
    
    def get_all_runs(self) -> Dict[str, AgentRun]:
        """Get all runs"""
        return self.runs.copy()


class FileBackend:
    """File-based backend that saves to JSON"""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.runs: Dict[str, AgentRun] = {}
        self._load()
    
    def _load(self) -> None:
        """Load runs from file"""
        try:
            with open(self.filepath, 'r') as f:
                data = json.load(f)
                # Handle both single dict and list of dicts
                if isinstance(data, list):
                    for run_data in data:
                        run = AgentRun.from_dict(run_data)
                        self.runs[run.run_id] = run
                elif isinstance(data, dict):
                    run = AgentRun.from_dict(data)
                    self.runs[run.run_id] = run
        except FileNotFoundError:
            pass
        except json.JSONDecodeError:
            # File exists but is invalid JSON, start fresh
            pass
    
    def _save(self) -> None:
        """Save runs to file"""
        with open(self.filepath, 'w') as f:
            json.dump([run.to_dict() for run in self.runs.values()], f, indent=2)
    
    def start_run(self, run: AgentRun) -> None:
        self.runs[run.run_id] = run
        self._save()
    
    def log_step(self, run_id: str, step: AgentStep) -> None:
        if run_id in self.runs:
            self.runs[run_id].steps.append(step)
            self._save()
    
    def log_error(self, run_id: str, error: str) -> None:
        if run_id in self.runs:
            self.runs[run_id].status = "error"
            self.runs[run_id].error = error
            self.runs[run_id].end_time = datetime.utcnow().isoformat()
            self._save()
    
    def end_run(self, run_id: str, final_output: str) -> None:
        if run_id in self.runs:
            self.runs[run_id].final_output = final_output
            self.runs[run_id].status = "success"
            self.runs[run_id].end_time = datetime.utcnow().isoformat()
            self._save()
    
    def get_run(self, run_id: str) -> Optional[AgentRun]:
        return self.runs.get(run_id)
    
    def get_all_runs(self) -> Dict[str, AgentRun]:
        """Get all runs"""
        return self.runs.copy()


class Tracer:
    """Simple tracer for agent runs"""
    
    def __init__(self, backend: Optional[Any] = None):
        self.backend = backend or InMemoryBackend()
        self.current_runs: Dict[str, AgentRun] = {}
    
    def start_run(self, metadata: Dict[str, Any]) -> str:
        """Start a new agent run"""
        run_id = f"run_{int(time.time() * 1000)}"
        
        run = AgentRun(
            run_id=run_id,
            metadata=metadata,
            start_time=datetime.utcnow().isoformat()
        )
        
        self.current_runs[run_id] = run
        self.backend.start_run(run)
        
        return run_id
    
    def log_step(self, run_id: str, step: Dict[str, Any]) -> None:
        """Log a step in the run"""
        if run_id not in self.current_runs:
            # Try to load from backend
            run = self.backend.get_run(run_id)
            if run:
                self.current_runs[run_id] = run
            else:
                raise ValueError(f"Run {run_id} not found")
        
        agent_step = AgentStep(
            step_id=step.get("step_id", len(self.current_runs[run_id].steps) + 1),
            timestamp=step.get("timestamp", datetime.utcnow().isoformat()),
            tool_name=step["tool_name"],
            tool_input=step["tool_input"],
            tool_output=step["tool_output"],
            messages_at_step=step.get("messages_at_step", [])
        )
        
        self.current_runs[run_id].steps.append(agent_step)
        self.backend.log_step(run_id, agent_step)
    
    def log_error(self, run_id: str, error: str) -> None:
        """Log an error in the run"""
        if run_id not in self.current_runs:
            run = self.backend.get_run(run_id)
            if run:
                self.current_runs[run_id] = run
            else:
                raise ValueError(f"Run {run_id} not found")
        
        run = self.current_runs[run_id]
        run.status = "error"
        run.error = error
        run.end_time = datetime.utcnow().isoformat()
        
        self.backend.log_error(run_id, error)
    
    def end_run(self, run_id: str, final_output: str) -> None:
        """End a run with final output"""
        if run_id not in self.current_runs:
            run = self.backend.get_run(run_id)
            if run:
                self.current_runs[run_id] = run
            else:
                raise ValueError(f"Run {run_id} not found")
        
        run = self.current_runs[run_id]
        run.final_output = final_output
        run.status = "success"
        run.end_time = datetime.utcnow().isoformat()
        
        self.backend.end_run(run_id, final_output)
    
    def get_run(self, run_id: str) -> Optional[AgentRun]:
        """Get a run by ID"""
        if run_id in self.current_runs:
            return self.current_runs[run_id]
        return self.backend.get_run(run_id)

