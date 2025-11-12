"""Tests for anomaly detector"""

import pytest
import os
import sqlite3
from datetime import datetime, timedelta
from src import AnomalyDetector, ObservabilityLogger


def test_anomaly_detector_initialization():
    """Test anomaly detector initializes correctly"""
    detector = AnomalyDetector()
    assert detector.db_path == "observability.db"


def test_token_spike_detection():
    """Test detection of token spikes"""
    db_path = "test_observability.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    
    logger = ObservabilityLogger(db_path=db_path)
    
    # Create historical data (24 hours ago)
    historical_time = (datetime.utcnow() - timedelta(hours=12)).isoformat()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    for i in range(10):
        cursor.execute("""
            INSERT INTO llm_calls (
                timestamp, request_id, prompt_version, model, prompt, response,
                input_tokens, output_tokens, total_tokens, latency_ms, cost_usd,
                status, error, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            historical_time,
            f"hist-{i}",
            "v1",
            "gpt-3.5-turbo",
            "Test",
            "Test",
            100, 100, 200, 500.0, 0.001,
            "success",
            None,
            "{}"
        ))
    conn.commit()
    conn.close()
    
    # Create recent data with spike (1 hour ago)
    recent_time = (datetime.utcnow() - timedelta(minutes=30)).isoformat()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    for i in range(10):
        cursor.execute("""
            INSERT INTO llm_calls (
                timestamp, request_id, prompt_version, model, prompt, response,
                input_tokens, output_tokens, total_tokens, latency_ms, cost_usd,
                status, error, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            recent_time,
            f"recent-{i}",
            "v1",
            "gpt-3.5-turbo",
            "Test",
            "Test",
            300, 300, 600, 500.0, 0.001,  # 3x tokens
            "success",
            None,
            "{}"
        ))
    conn.commit()
    conn.close()
    
    # Check for anomalies
    detector = AnomalyDetector(db_path=db_path)
    anomalies = detector.check_anomalies()
    
    # Should detect token spike
    token_spikes = [a for a in anomalies if a["type"] == "token_spike"]
    assert len(token_spikes) > 0
    
    # Cleanup
    os.remove(db_path)

