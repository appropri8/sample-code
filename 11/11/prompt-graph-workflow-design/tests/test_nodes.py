"""Tests for node implementations"""

import pytest
from src.nodes import (
    NodeStatus,
    NodeResult,
    PromptNode,
    RetrievalNode,
    DecisionNode,
    ToolNode,
    MemoryNode,
    TransformNode
)


def test_node_result():
    """Test NodeResult dataclass"""
    result = NodeResult(
        status=NodeStatus.SUCCESS,
        output={"key": "value"},
        metadata={"test": True}
    )
    assert result.status == NodeStatus.SUCCESS
    assert result.output["key"] == "value"
    assert result.metadata["test"] is True


def test_retrieval_node_mock():
    """Test RetrievalNode with mock function"""
    def mock_retrieval(query: str, top_k: int):
        return [f"Doc {i} about {query}" for i in range(top_k)]
    
    node = RetrievalNode(
        node_id="test_retrieval",
        query_field="query",
        top_k=3,
        retrieval_function=mock_retrieval
    )
    
    result = node.execute({"query": "test"})
    assert result.status == NodeStatus.SUCCESS
    assert "context" in result.output
    assert len(result.output["documents"]) == 3


def test_retrieval_node_missing_input():
    """Test RetrievalNode with missing input"""
    node = RetrievalNode(
        node_id="test_retrieval",
        query_field="query",
        top_k=3
    )
    
    result = node.execute({})
    assert result.status == NodeStatus.FAILED
    assert "Missing required inputs" in result.error


def test_decision_node():
    """Test DecisionNode"""
    node = DecisionNode(
        node_id="test_decision",
        condition="value < 10",
        true_branch="branch_a",
        false_branch="branch_b",
        inputs=["value"]
    )
    
    # Test true branch
    result = node.execute({"value": 5})
    assert result.status == NodeStatus.SUCCESS
    assert result.output["branch"] == "branch_a"
    assert result.output["condition_result"] is True
    
    # Test false branch
    result = node.execute({"value": 15})
    assert result.status == NodeStatus.SUCCESS
    assert result.output["branch"] == "branch_b"
    assert result.output["condition_result"] is False


def test_tool_node():
    """Test ToolNode"""
    def add_numbers(a: int, b: int) -> int:
        return a + b
    
    node = ToolNode(
        node_id="test_tool",
        tool_function=add_numbers,
        inputs=["a", "b"]
    )
    
    result = node.execute({"a": 5, "b": 3})
    assert result.status == NodeStatus.SUCCESS
    assert result.output["result"] == 8


def test_memory_node():
    """Test MemoryNode"""
    memory_store = {}
    
    # Write node
    write_node = MemoryNode(
        node_id="write_memory",
        operation="write",
        key="test_key",
        inputs=["data"],
        memory_store=memory_store
    )
    
    result = write_node.execute({"data": "test_value"})
    assert result.status == NodeStatus.SUCCESS
    assert memory_store["test_key"]["data"] == "test_value"
    
    # Read node
    read_node = MemoryNode(
        node_id="read_memory",
        operation="read",
        key="test_key",
        memory_store=memory_store
    )
    
    result = read_node.execute({})
    assert result.status == NodeStatus.SUCCESS
    assert result.output["memory_result"]["data"] == "test_value"


def test_transform_node():
    """Test TransformNode"""
    def uppercase_transform(inputs: dict) -> dict:
        return {k: v.upper() if isinstance(v, str) else v for k, v in inputs.items()}
    
    node = TransformNode(
        node_id="test_transform",
        transform_function=uppercase_transform,
        inputs=["text"]
    )
    
    result = node.execute({"text": "hello"})
    assert result.status == NodeStatus.SUCCESS
    assert result.output["text"] == "HELLO"

