"""Time-travel debugging: resume, fork, compare."""
import uuid
from typing import Dict, Any, List
from .checkpoint_store import CheckpointStore
from .events import StepEvent
from .agent import Agent


def resume_from_checkpoint(
    run_id: str,
    step_id: str,
    checkpoint_store: CheckpointStore,
    tools: Dict[str, Any]
) -> Dict[str, Any]:
    """Resume agent execution from a checkpoint."""
    checkpoint = checkpoint_store.load_checkpoint(run_id, step_id)
    if not checkpoint:
        raise ValueError(f"Checkpoint not found: {run_id}/{step_id}")
    
    # Create agent with restored state
    agent = Agent(
        tools=tools,
        checkpoint_store=checkpoint_store,
        run_id=f"{run_id}_resume_{uuid.uuid4().hex[:8]}",
        state=checkpoint.state.copy(),
        messages=checkpoint.messages.copy()
    )
    agent.step_number = checkpoint.step_number
    
    # Continue execution
    result = agent.run(checkpoint.state.get("query", ""), max_steps=10)
    
    return result


def fork_run(
    run_id: str,
    step_id: str,
    state_modifications: Dict[str, Any],
    checkpoint_store: CheckpointStore,
    tools: Dict[str, Any]
) -> tuple[str, Dict[str, Any]]:
    """Fork a run with modified state."""
    checkpoint = checkpoint_store.load_checkpoint(run_id, step_id)
    if not checkpoint:
        raise ValueError(f"Checkpoint not found: {run_id}/{step_id}")
    
    # Apply modifications
    state = checkpoint.state.copy()
    state.update(state_modifications)
    
    # Create new run ID for fork
    fork_run_id = f"{run_id}_fork_{uuid.uuid4().hex[:8]}"
    
    # Create agent with modified state
    agent = Agent(
        tools=tools,
        checkpoint_store=checkpoint_store,
        run_id=fork_run_id,
        state=state,
        messages=checkpoint.messages.copy()
    )
    agent.step_number = checkpoint.step_number
    
    # Continue execution
    result = agent.run(state.get("query", ""), max_steps=10)
    
    return fork_run_id, result


def compare_runs(
    run_id_1: str,
    run_id_2: str,
    checkpoint_store: CheckpointStore
) -> Dict[str, Any]:
    """Compare two runs and find where they diverged."""
    events_1 = checkpoint_store.load_events(run_id_1)
    events_2 = checkpoint_store.load_events(run_id_2)
    
    divergence_point = None
    divergence_details = {}
    
    for i, (e1, e2) in enumerate(zip(events_1, events_2)):
        if e1.tool_name != e2.tool_name or e1.tool_args != e2.tool_args:
            divergence_point = i
            divergence_details = {
                "step_number": i + 1,
                "run_1": {
                    "tool": e1.tool_name,
                    "args": e1.tool_args,
                    "result": e1.tool_result
                },
                "run_2": {
                    "tool": e2.tool_name,
                    "args": e2.tool_args,
                    "result": e2.tool_result
                }
            }
            break
    
    if divergence_point is None:
        return {
            "diverged": False,
            "message": "Runs are identical"
        }
    
    return {
        "diverged": True,
        "divergence_point": divergence_point,
        "details": divergence_details
    }


def diff_tool_sequences(
    run_id_1: str,
    run_id_2: str,
    checkpoint_store: CheckpointStore
) -> List[Dict[str, Any]]:
    """Diff tool sequences between two runs."""
    events_1 = checkpoint_store.load_events(run_id_1)
    events_2 = checkpoint_store.load_events(run_id_2)
    
    diff = []
    max_len = max(len(events_1), len(events_2))
    
    for i in range(max_len):
        e1 = events_1[i] if i < len(events_1) else None
        e2 = events_2[i] if i < len(events_2) else None
        
        if e1 and e2:
            if e1.tool_name == e2.tool_name and e1.tool_args == e2.tool_args:
                diff.append({
                    "step": i + 1,
                    "status": "same",
                    "tool": e1.tool_name
                })
            else:
                diff.append({
                    "step": i + 1,
                    "status": "different",
                    "run_1": {"tool": e1.tool_name, "args": e1.tool_args},
                    "run_2": {"tool": e2.tool_name, "args": e2.tool_args}
                })
        elif e1:
            diff.append({
                "step": i + 1,
                "status": "only_in_run_1",
                "tool": e1.tool_name
            })
        elif e2:
            diff.append({
                "step": i + 1,
                "status": "only_in_run_2",
                "tool": e2.tool_name
            })
    
    return diff
