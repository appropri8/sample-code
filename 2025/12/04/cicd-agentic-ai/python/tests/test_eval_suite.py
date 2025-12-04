"""Evaluation suite for end-to-end testing"""
import pytest
from src.agent import Agent, AgentRole
from src.workflow import Workflow, WorkflowNode


EVAL_CASES = [
    {
        "name": "update_user_billing_plan",
        "input": {"input": "Update user 123 to premium plan"},
        "expected": {
            "tools_called": ["get_user", "update_billing"],
            "forbidden_tools": ["delete_user", "escalate"],
            "max_latency_ms": 5000,
            "max_tokens": 5000
        }
    },
    {
        "name": "escalate_complex_issue",
        "input": {"input": "User reports critical bug in payment system"},
        "expected": {
            "tools_called": ["search_kb", "escalate"],
            "forbidden_tools": [],
            "max_latency_ms": 10000
        }
    }
]


def create_test_workflow():
    """Create test workflow"""
    planner = Agent(
        role=AgentRole.PLANNER,
        model_config={"model": "gpt-4", "temperature": 0.7},
        tools=["search_kb", "create_ticket", "escalate", "get_user", "update_billing"],
        version="1.0.0"
    )
    
    worker = Agent(
        role=AgentRole.WORKER,
        model_config={"model": "gpt-4", "temperature": 0.7},
        tools=["search_kb", "create_ticket", "escalate", "get_user", "update_billing"],
        version="1.0.0"
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
        version="1.0.0"
    )


@pytest.mark.parametrize("case", EVAL_CASES)
def test_eval_suite(case):
    """Run evaluation suite against workflow"""
    workflow = create_test_workflow()
    
    result = workflow.execute(case["input"])
    
    # Check tools called
    tools_called = []
    for node_result in result.values():
        if isinstance(node_result, dict) and "tools_called" in node_result:
            tools_called.extend(node_result["tools_called"])
    
    # Check expected tools
    for tool in case["expected"]["tools_called"]:
        assert tool in tools_called or any(
            tool in str(v) for v in result.values()
        ), f"Expected tool {tool} not called"
    
    # Check forbidden tools
    for tool in case["expected"].get("forbidden_tools", []):
        assert tool not in tools_called, f"Forbidden tool {tool} was called"
    
    # Check latency (if available)
    latency = result.get("latency_ms", 0)
    if latency > 0:
        assert latency <= case["expected"]["max_latency_ms"], \
            f"Latency {latency}ms exceeds max {case['expected']['max_latency_ms']}ms"

