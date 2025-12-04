"""Example: Canary deployment"""
from src.agent import Agent, AgentRole
from src.workflow import Workflow, WorkflowNode
from src.deployment.canary import CanaryDeployment
import random


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
        model_config={"model": "gpt-4", "temperature": 0.5},
        tools=["search_kb", "create_ticket", "escalate"],
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
    """Run canary deployment example"""
    baseline = create_baseline_workflow()
    candidate = create_candidate_workflow()
    
    canary = CanaryDeployment(
        baseline_workflow=baseline,
        candidate_workflow=candidate,
        canary_percentage=0.1,  # 10% for demo
        rollback_conditions={
            "error_rate_threshold": 0.05,
            "latency_threshold_ms": 10000,
            "cost_threshold_multiplier": 2.0
        }
    )
    
    # Simulate requests
    print("Simulating 100 requests...")
    for i in range(100):
        test_input = {
            "input": f"Request {i}: User needs help",
            "trace_id": f"trace_{i}"
        }
        
        result = canary.route(test_input)
        
        if i % 20 == 0:
            metrics = canary.get_metrics()
            print(f"\nAfter {i} requests:")
            print(f"Canary requests: {metrics['canary']['requests']}")
            print(f"Baseline requests: {metrics['baseline']['requests']}")
            print(f"Rolled back: {metrics['rolled_back']}")
    
    # Final metrics
    metrics = canary.get_metrics()
    print("\n=== Final Metrics ===")
    print(f"Canary: {metrics['canary']}")
    print(f"Baseline: {metrics['baseline']}")
    print(f"Rolled back: {metrics['rolled_back']}")


if __name__ == "__main__":
    main()

