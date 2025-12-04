"""Example: Shadow deployment"""
from src.agent import Agent, AgentRole
from src.workflow import Workflow, WorkflowNode
from src.deployment.shadow import ShadowDeployment


def create_baseline_workflow():
    """Create baseline workflow"""
    planner = Agent(
        role=AgentRole.PLANNER,
        model_config={"model": "gpt-4", "temperature": 0.7},
        tools=["search_kb", "create_ticket"],
        version="1.2.0"
    )
    
    worker = Agent(
        role=AgentRole.WORKER,
        model_config={"model": "gpt-4", "temperature": 0.7},
        tools=["search_kb", "create_ticket"],
        version="1.2.0"
    )
    
    nodes = [
        WorkflowNode("planner", planner),
        WorkflowNode("worker", worker)
    ]
    
    edges = [("planner", "worker")]
    
    return Workflow(
        name="support",
        nodes=nodes,
        edges=edges,
        version="1.2.0"
    )


def create_candidate_workflow():
    """Create candidate workflow"""
    planner = Agent(
        role=AgentRole.PLANNER,
        model_config={"model": "gpt-4", "temperature": 0.5},  # Different temp
        tools=["search_kb", "create_ticket", "escalate"],  # New tool
        version="1.3.0"
    )
    
    worker = Agent(
        role=AgentRole.WORKER,
        model_config={"model": "gpt-4", "temperature": 0.5},
        tools=["search_kb", "create_ticket", "escalate"],
        version="1.3.0"
    )
    
    nodes = [
        WorkflowNode("planner", planner),
        WorkflowNode("worker", worker)
    ]
    
    edges = [("planner", "worker")]
    
    return Workflow(
        name="support",
        nodes=nodes,
        edges=edges,
        version="1.3.0"
    )


def main():
    """Run shadow deployment example"""
    baseline = create_baseline_workflow()
    candidate = create_candidate_workflow()
    
    shadow = ShadowDeployment(
        baseline_workflow=baseline,
        candidate_workflow=candidate,
        comparison_metrics=["latency_ms", "tools_called", "success"]
    )
    
    # Run shadow on test input
    test_input = {
        "input": "User wants to reset password",
        "trace_id": "test_trace_001"
    }
    
    result = shadow.run_shadow(test_input)
    
    print("Shadow deployment result:")
    print(f"Baseline result: {result}")
    
    # Get comparison summary
    summary = shadow.get_comparison_summary()
    print(f"\nComparison summary: {summary}")


if __name__ == "__main__":
    main()

