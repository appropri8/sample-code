"""Tests for observability logger"""

import pytest
import os
import sqlite3
from src import ObservabilityLogger


def test_logger_initialization():
    """Test logger initializes database correctly"""
    db_path = "test_observability.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    
    logger = ObservabilityLogger(db_path=db_path)
    
    # Check database exists and has correct schema
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='llm_calls'")
    assert cursor.fetchone() is not None
    conn.close()
    
    # Cleanup
    os.remove(db_path)


def test_log_llm_call():
    """Test logging an LLM call"""
    db_path = "test_observability.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    
    logger = ObservabilityLogger(db_path=db_path)
    
    log_entry = logger.log_llm_call(
        request_id="test-123",
        prompt_version="v1",
        model="gpt-3.5-turbo",
        prompt="Test prompt",
        response="Test response",
        usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
        latency_ms=500.0,
        status="success"
    )
    
    assert log_entry.request_id == "test-123"
    assert log_entry.total_tokens == 30
    assert log_entry.cost_usd > 0
    
    # Check database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM llm_calls WHERE request_id = 'test-123'")
    assert cursor.fetchone()[0] == 1
    conn.close()
    
    # Cleanup
    os.remove(db_path)


def test_cost_calculation():
    """Test cost calculation for different models"""
    db_path = "test_observability.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    
    logger = ObservabilityLogger(db_path=db_path)
    
    # Test gpt-4 (more expensive)
    log1 = logger.log_llm_call(
        request_id="test-1",
        prompt_version="v1",
        model="gpt-4",
        prompt="Test",
        response="Test",
        usage={"prompt_tokens": 1000, "completion_tokens": 1000, "total_tokens": 2000},
        latency_ms=1000.0,
        status="success"
    )
    
    # Test gpt-3.5-turbo (cheaper)
    log2 = logger.log_llm_call(
        request_id="test-2",
        prompt_version="v1",
        model="gpt-3.5-turbo",
        prompt="Test",
        response="Test",
        usage={"prompt_tokens": 1000, "completion_tokens": 1000, "total_tokens": 2000},
        latency_ms=1000.0,
        status="success"
    )
    
    # gpt-4 should be more expensive
    assert log1.cost_usd > log2.cost_usd
    
    # Cleanup
    os.remove(db_path)

