"""Tests for graph structure"""

import pytest
from src.graph import PromptGraph
from src.nodes import RetrievalNode, DecisionNode, ToolNode


def test_create_graph():
    """Test creating a graph"""
    graph = PromptGraph("test_graph")
    assert graph.graph_id == "test_graph"
    assert len(graph.nodes) == 0
    assert len(graph.edges) == 0


def test_add_node():
    """Test adding nodes to graph"""
    graph = PromptGraph("test_graph")
    
    node1 = RetrievalNode(
        node_id="node1",
        query_field="query",
        top_k=5
    )
    
    node2 = DecisionNode(
        node_id="node2",
        condition="value > 0",
        true_branch="branch_a",
        false_branch="branch_b"
    )
    
    graph.add_node(node1)
    graph.add_node(node2)
    
    assert len(graph.nodes) == 2
    assert "node1" in graph.nodes
    assert "node2" in graph.nodes


def test_add_edge():
    """Test adding edges to graph"""
    graph = PromptGraph("test_graph")
    
    node1 = RetrievalNode(
        node_id="node1",
        query_field="query",
        top_k=5
    )
    
    node2 = DecisionNode(
        node_id="node2",
        condition="value > 0",
        true_branch="branch_a",
        false_branch="branch_b"
    )
    
    graph.add_node(node1)
    graph.add_node(node2)
    
    graph.add_edge("node1", "node2", {"context": "value"})
    
    assert len(graph.edges) == 1
    assert graph.edges[0][0] == "node1"
    assert graph.edges[0][1] == "node2"


def test_get_entry_nodes():
    """Test finding entry nodes"""
    graph = PromptGraph("test_graph")
    
    node1 = RetrievalNode(node_id="node1", query_field="query", top_k=5)
    node2 = DecisionNode(
        node_id="node2",
        condition="value > 0",
        true_branch="a",
        false_branch="b"
    )
    node3 = ToolNode(
        node_id="node3",
        tool_function=lambda x: x,
        inputs=["x"]
    )
    
    graph.add_node(node1)
    graph.add_node(node2)
    graph.add_node(node3)
    
    graph.add_edge("node1", "node2")
    graph.add_edge("node2", "node3")
    
    entry_nodes = graph.get_entry_nodes()
    assert "node1" in entry_nodes
    assert len(entry_nodes) == 1


def test_get_next_nodes():
    """Test getting next nodes"""
    graph = PromptGraph("test_graph")
    
    node1 = RetrievalNode(node_id="node1", query_field="query", top_k=5)
    node2 = DecisionNode(
        node_id="node2",
        condition="value > 0",
        true_branch="node3",
        false_branch="node4"
    )
    node3 = ToolNode(node_id="node3", tool_function=lambda: None, inputs=[])
    node4 = ToolNode(node_id="node4", tool_function=lambda: None, inputs=[])
    
    for node in [node1, node2, node3, node4]:
        graph.add_node(node)
    
    graph.add_edge("node1", "node2")
    graph.add_edge("node2", "node3", condition="value > 0")
    graph.add_edge("node2", "node4", condition="value <= 0")
    
    # Test with condition true
    next_nodes = graph.get_next_nodes("node2", {"value": 5})
    assert "node3" in next_nodes
    assert "node4" not in next_nodes
    
    # Test with condition false
    next_nodes = graph.get_next_nodes("node2", {"value": -5})
    assert "node4" in next_nodes
    assert "node3" not in next_nodes


def test_validate_graph():
    """Test graph validation"""
    graph = PromptGraph("test_graph")
    
    node1 = RetrievalNode(node_id="node1", query_field="query", top_k=5)
    node2 = DecisionNode(
        node_id="node2",
        condition="value > 0",
        true_branch="a",
        false_branch="b"
    )
    
    graph.add_node(node1)
    graph.add_node(node2)
    graph.add_edge("node1", "node2")
    
    is_valid, errors = graph.validate()
    assert is_valid
    assert len(errors) == 0


def test_validate_graph_invalid_edge():
    """Test graph validation with invalid edge"""
    graph = PromptGraph("test_graph")
    
    node1 = RetrievalNode(node_id="node1", query_field="query", top_k=5)
    graph.add_node(node1)
    
    # Try to add edge to non-existent node
    with pytest.raises(ValueError):
        graph.add_edge("node1", "nonexistent")

