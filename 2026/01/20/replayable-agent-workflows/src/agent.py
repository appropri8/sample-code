"""Minimal agent with step boundaries and event emission."""
import time
import uuid
from datetime import datetime
from typing import Dict, Any, List, Callable
from .events import StepEvent, Checkpoint
from .checkpoint_store import CheckpointStore
from .tool_recorder import ToolRecorder


class Agent:
    """Simple agent that emits events and checkpoints."""
    
    def __init__(
        self,
        tools: Dict[str, Callable],
        checkpoint_store: CheckpointStore,
        run_id: str = None,
        state: Dict[str, Any] = None,
        messages: List[Dict[str, str]] = None
    ):
        self.tools = tools
        self.checkpoint_store = checkpoint_store
        self.run_id = run_id or f"run_{uuid.uuid4().hex[:8]}"
        self.state = state or {}
        self.messages = messages or []
        self.step_number = 0
        self.agent_version = "v1.0"
        self.recorder = ToolRecorder(self.run_id)
    
    def run(self, query: str, max_steps: int = 10) -> Dict[str, Any]:
        """Run agent with query."""
        self.messages.append({"role": "user", "content": query})
        self.state["query"] = query
        
        for _ in range(max_steps):
            # Decide next action
            decision = self._decide_next_action()
            
            if decision["action"] == "finish":
                break
            
            # Execute step
            self._execute_step(decision)
        
        # Save final recordings
        self.recorder.save()
        
        return {
            "run_id": self.run_id,
            "answer": self.state.get("answer", "No answer generated"),
            "steps": self.step_number
        }
    
    def _decide_next_action(self) -> Dict[str, Any]:
        """Decide next action based on state."""
        # Simple decision logic
        if "docs" not in self.state:
            return {"action": "tool", "tool": "search_docs"}
        elif "answer" not in self.state:
            return {"action": "tool", "tool": "generate_answer"}
        else:
            return {"action": "finish"}
    
    def _execute_step(self, decision: Dict[str, Any]):
        """Execute a single step and emit event."""
        self.step_number += 1
        step_id = f"step_{self.step_number}"
        
        # Capture input state
        input_state = self.state.copy()
        
        # Execute tool
        start_time = time.time()
        tool_name = decision["tool"]
        tool_func = self.tools[tool_name]
        
        # Prepare tool args
        if tool_name == "search_docs":
            tool_args = {"query": self.state["query"]}
        elif tool_name == "generate_answer":
            tool_args = {
                "query": self.state["query"],
                "docs": self.state.get("docs", [])
            }
        else:
            tool_args = {}
        
        # Call tool
        tool_result = tool_func(**tool_args)
        duration_ms = (time.time() - start_time) * 1000
        
        # Record tool call
        self.recorder.record(tool_name, tool_args, tool_result)
        
        # Update state
        if tool_name == "search_docs":
            self.state["docs"] = tool_result.get("docs", [])
        elif tool_name == "generate_answer":
            self.state["answer"] = tool_result.get("answer", "")
        
        output_state = self.state.copy()
        
        # Emit event
        event = StepEvent(
            step_id=step_id,
            run_id=self.run_id,
            step_number=self.step_number,
            input_state=input_state,
            decision=decision["action"],
            tool_name=tool_name,
            tool_args=tool_args,
            tool_result=tool_result,
            output_state=output_state,
            timestamp=datetime.now(),
            duration_ms=duration_ms
        )
        self.checkpoint_store.save_event(event)
        
        # Save checkpoint
        checkpoint = Checkpoint(
            run_id=self.run_id,
            step_id=step_id,
            step_number=self.step_number,
            timestamp=datetime.now(),
            messages=self.messages.copy(),
            tool_calls=[{
                "tool": tool_name,
                "args": tool_args,
                "result": tool_result
            }],
            model_config={},
            state=output_state,
            agent_version=self.agent_version
        )
        self.checkpoint_store.save_checkpoint(checkpoint)


def replay_run(run_id: str, checkpoint_store: CheckpointStore) -> List[StepEvent]:
    """Replay a run from recorded events."""
    events = checkpoint_store.load_events(run_id)
    
    print(f"Replaying run {run_id} ({len(events)} steps)")
    for event in events:
        print(f"  Step {event.step_number}: {event.tool_name}({event.tool_args})")
        print(f"    Result: {event.tool_result}")
        print(f"    Duration: {event.duration_ms:.2f}ms")
    
    return events
