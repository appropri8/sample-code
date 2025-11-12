"""Tests for monitoring module"""

import pytest
import os
import json
from src.monitoring import count_tokens, estimate_cost, RAGLogger


def test_count_tokens():
    """Test token counting"""
    text = "This is a test"
    count = count_tokens(text)
    assert isinstance(count, int)
    assert count > 0


def test_count_tokens_empty():
    """Test counting tokens in empty text"""
    count = count_tokens("")
    assert count == 0


def test_estimate_cost_gpt4():
    """Test cost estimation for GPT-4"""
    cost = estimate_cost(1000, 500, "gpt-4")
    # GPT-4: $0.03/1k prompt, $0.06/1k completion
    # 1000 prompt tokens = $0.03, 500 completion tokens = $0.03
    # Total = $0.06
    assert cost == 0.06


def test_estimate_cost_gpt35():
    """Test cost estimation for GPT-3.5"""
    cost = estimate_cost(1000, 500, "gpt-3.5-turbo")
    # GPT-3.5: $0.0015/1k prompt, $0.002/1k completion
    # 1000 prompt tokens = $0.0015, 500 completion tokens = $0.001
    # Total = $0.0025
    assert cost == 0.0025


def test_rag_logger():
    """Test RAG logger"""
    log_file = "test_logs.jsonl"
    logger = RAGLogger(log_file)
    
    # Clean up if file exists
    if os.path.exists(log_file):
        os.remove(log_file)
    
    logger.log_request(
        query="Test query",
        retrieved_chunks=[{"text": "Chunk 1"}],
        response="Test response",
        token_counts={"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
        cost=0.01,
        latency=1.5
    )
    
    # Verify log file was created
    assert os.path.exists(log_file)
    
    # Read and verify log entry
    with open(log_file, "r") as f:
        line = f.readline()
        entry = json.loads(line)
        assert entry["query"] == "Test query"
        assert entry["total_tokens"] == 150
        assert entry["cost"] == 0.01
    
    # Clean up
    os.remove(log_file)


def test_rag_logger_stats():
    """Test getting statistics from logger"""
    log_file = "test_stats_logs.jsonl"
    logger = RAGLogger(log_file)
    
    # Clean up if file exists
    if os.path.exists(log_file):
        os.remove(log_file)
    
    # Log multiple requests
    for i in range(3):
        logger.log_request(
            query=f"Query {i}",
            retrieved_chunks=[],
            response=f"Response {i}",
            token_counts={"total_tokens": 100, "completion_tokens": 50},
            cost=0.01,
            latency=1.0
        )
    
    stats = logger.get_stats()
    assert stats["total_requests"] == 3
    assert stats["total_tokens"] == 300
    assert stats["total_cost"] == 0.03
    assert stats["avg_latency_ms"] == 1000.0
    
    # Clean up
    os.remove(log_file)

