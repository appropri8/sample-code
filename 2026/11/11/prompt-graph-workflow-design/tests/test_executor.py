"""Tests for graph executor"""

import pytest
from src.graph import PromptGraph
from src.executor import GraphExecutor
from src.nodes import (
    RetrievalNode,
    DecisionNode,
    ToolNode,
    NodeStatus
)


def test_simple_execution():
    """Test simple linear execution"""
    graph = PromptGraph("test_graph")
    
    def mock_retrieval(query: str, top_k: int):
        return [f"Doc about {query}"]
    
    node1 = RetrievalNode(
        node_id="retrieve",
        query_field="query",
        top_k=1,
        retrieval_function=mock_retrieval
    )
    
    def process(context: str) -> str:
        return f"Processed: {context}"
    
    node2 = ToolNode(
        node_id="process",
        tool_function=process,
        inputs=["context"]
    )
    
    graph.add_node(node1)
    graph.add_node(node2)
    graph.add_edge("retrieve", "process", {"context": "context"})
    
    executor = GraphExecutor(graph)
    result = executor.execute({"query": "test"})
    
    assert "result" in result
    assert "Processed: Doc about test" in result["result"]


def test_branching_execution():
    """Test execution with branching"""
    graph = PromptGraph("test_graph")
    
    node1 = DecisionNode(
        node_id="decision",
        condition="value > 5",
        true_branch="high",
        false_branch="low",
        inputs=["value"]
    )
    
    def high_func() -> str:
        return "high_value"
    
    def low_func() -> str:
        return "low_value"
    
    node2 = ToolNode(node_id="high", tool_function=high_func, inputs=[])
    node3 = ToolNode(node_id="low", tool_function=low_func, inputs=[])
    
    graph.add_node(node1)
    graph.add_node(node2)
    graph.add_node(node3)
    
    graph.add_edge("decision", "high", condition="value > 5")
    graph.add_edge("decision", "low", condition="value <= 5")
    
    executor = GraphExecutor(graph)
    
    # Test high branch
    result = executor.execute({"value": 10})
    assert "result" in result
    assert result["result"] == "high_value"
    
    # Test low branch
    executor = GraphExecutor(graph)
    result = executor.execute({"value": 3})
    assert "result" in result
    assert result["result"] == "low_value"


def test_execution_with_failure():
    """Test execution handling node failures"""
    graph = PromptGraph("test_graph")
    
    def failing_tool() -> str:
        raise ValueError("Tool failed")
    
    node1 = ToolNode(
        node_id="failing",
        tool_function=failing_tool,
        inputs=[]
    )
    
    def fallback() -> str:
        return "fallback_result"
    
    node2 = ToolNode(
        node_id="fallback",
        tool_function=fallback,
        inputs=[]
    )
    
    graph.add_node(node1)
    graph.add_node(node2)
    graph.add_edge("failing", "fallback", condition="error_occurred")
    
    executor = GraphExecutor(graph)
    result = executor.execute({})
    
    # Should have fallback result
    assert "result" in result
    assert result["result"] == "fallback_result"
    assert executor.node_results["failing"].status == NodeStatus.FAILED


def test_dependencies_ready():
    """Test dependency checking"""
    graph = PromptGraph("test_graph")
    
    node1 = ToolNode(
        node_id="node1",
        tool_function=lambda: "result1",
        inputs=[]
    )
    
    node2 = ToolNode(
        node_id="node2",
        tool_function=lambda x: f"processed_{x}",
        inputs=["input"]
    )
    
    graph.add_node(node1)
    graph.add_node(node2)
    graph.add_edge("node1", "node2", {"result": "input"})
    
    executor = GraphExecutor(graph)
    
    # Check dependencies
    assert not executor._dependencies_ready("node2")  # node1 hasn't executed
    executor.execute({})
    assert executor._dependencies_ready("node2")  # Now node1 has executed

