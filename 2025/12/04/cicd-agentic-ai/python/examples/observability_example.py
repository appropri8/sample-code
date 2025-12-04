"""Example: Observability with logging and metrics"""
from src.agent import Agent, AgentRole
from src.workflow import Workflow, WorkflowNode
from src.observability.logging import AgentLogger, generate_trace_id
from src.observability.metrics import track_agent_execution, metrics


def create_workflow():
    """Create example workflow"""
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


def main():
    """Run observability example"""
    logger = AgentLogger()
    workflow = create_workflow()
    
    # Generate trace ID
    trace_id = generate_trace_id()
    
    # Execute workflow
    test_input = {
        "input": "User wants to reset password",
        "trace_id": trace_id
    }
    
    result = workflow.execute(test_input)
    
    # Log workflow execution
    logger.log_agent_execution(
        trace_id=trace_id,
        agent_version="1.2.0",
        input=test_input,
        output=result,
        latency_ms=result.get("latency_ms", 0),
        success=result.get("success", True),
        tokens_used=1000,
        cost=0.01
    )
    
    # Track metrics
    track_agent_execution(
        agent_version="1.2.0",
        success=result.get("success", True),
        latency_ms=result.get("latency_ms", 0),
        tokens_used=1000,
        cost=0.01
    )
    
    # Get metrics
    all_metrics = metrics.get_metrics()
    print("=== Metrics ===")
    print(f"Counters: {all_metrics['counters']}")
    print(f"Gauges: {all_metrics['gauges']}")
    print(f"Histograms: {all_metrics['histograms']}")


if __name__ == "__main__":
    main()

