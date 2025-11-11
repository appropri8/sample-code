"""Anomaly detection for LLM observability"""

import sqlite3
from typing import List, Dict, Any


class AnomalyDetector:
    """Detect anomalies in LLM observability data"""
    
    def __init__(self, db_path: str = "observability.db"):
        self.db_path = db_path
    
    def check_anomalies(self) -> List[Dict[str, Any]]:
        """Check for various types of anomalies"""
        anomalies = []
        conn = sqlite3.connect(self.db_path)
        
        # Check for token spike
        cursor = conn.cursor()
        cursor.execute("""
            SELECT prompt_version, AVG(total_tokens) as avg_tokens
            FROM llm_calls
            WHERE timestamp > datetime('now', '-1 hour')
            GROUP BY prompt_version
        """)
        recent_avgs = {row[0]: row[1] for row in cursor.fetchall()}
        
        cursor.execute("""
            SELECT prompt_version, AVG(total_tokens) as avg_tokens
            FROM llm_calls
            WHERE timestamp > datetime('now', '-24 hours')
              AND timestamp < datetime('now', '-1 hour')
            GROUP BY prompt_version
        """)
        historical_avgs = {row[0]: row[1] for row in cursor.fetchall()}
        
        for version, recent_avg in recent_avgs.items():
            historical_avg = historical_avgs.get(version, recent_avg)
            if historical_avg > 0 and recent_avg > historical_avg * 1.5:
                anomalies.append({
                    "type": "token_spike",
                    "prompt_version": version,
                    "recent_avg": recent_avg,
                    "historical_avg": historical_avg,
                    "increase_percent": ((recent_avg - historical_avg) / historical_avg) * 100
                })
        
        # Check for cost spike
        cursor.execute("""
            SELECT SUM(cost_usd) as total_cost
            FROM llm_calls
            WHERE timestamp > datetime('now', '-1 hour')
        """)
        recent_cost = cursor.fetchone()[0] or 0
        
        cursor.execute("""
            SELECT SUM(cost_usd) as total_cost
            FROM llm_calls
            WHERE timestamp > datetime('now', '-24 hours')
              AND timestamp < datetime('now', '-1 hour')
        """)
        historical_total = cursor.fetchone()[0] or 0
        historical_hourly_cost = historical_total / 23 if historical_total > 0 else 0
        
        if historical_hourly_cost > 0 and recent_cost > historical_hourly_cost * 2:
            anomalies.append({
                "type": "cost_spike",
                "recent_cost": recent_cost,
                "historical_avg": historical_hourly_cost,
                "increase_percent": ((recent_cost - historical_hourly_cost) / historical_hourly_cost) * 100
            })
        
        # Check for latency increase
        cursor.execute("""
            SELECT AVG(latency_ms) as avg_latency
            FROM llm_calls
            WHERE timestamp > datetime('now', '-1 hour')
        """)
        recent_latency = cursor.fetchone()[0] or 0
        
        cursor.execute("""
            SELECT AVG(latency_ms) as avg_latency
            FROM llm_calls
            WHERE timestamp > datetime('now', '-24 hours')
              AND timestamp < datetime('now', '-1 hour')
        """)
        historical_latency = cursor.fetchone()[0] or 0
        
        if historical_latency > 0 and recent_latency > historical_latency * 1.5:
            anomalies.append({
                "type": "latency_spike",
                "recent_latency": recent_latency,
                "historical_latency": historical_latency,
                "increase_percent": ((recent_latency - historical_latency) / historical_latency) * 100
            })
        
        # Check for branch rate change
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN condition_result = 1 THEN 1 ELSE 0 END) * 1.0 / COUNT(*) as human_review_rate
            FROM branch_decisions
            WHERE timestamp > datetime('now', '-1 hour')
              AND condition LIKE '%confidence%'
        """)
        recent_human_rate = cursor.fetchone()[0] or 0
        
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN condition_result = 1 THEN 1 ELSE 0 END) * 1.0 / COUNT(*) as human_review_rate
            FROM branch_decisions
            WHERE timestamp > datetime('now', '-24 hours')
              AND timestamp < datetime('now', '-1 hour')
              AND condition LIKE '%confidence%'
        """)
        historical_human_rate = cursor.fetchone()[0] or 0
        
        if abs(recent_human_rate - historical_human_rate) > 0.2:
            anomalies.append({
                "type": "branch_rate_change",
                "recent_rate": recent_human_rate,
                "historical_rate": historical_human_rate,
                "change": recent_human_rate - historical_human_rate
            })
        
        conn.close()
        return anomalies
    
    def alert(self, anomalies: List[Dict[str, Any]]):
        """Alert on detected anomalies"""
        if not anomalies:
            return
        
        print("ALERT: Anomalies detected!")
        for anomaly in anomalies:
            print(f"  - {anomaly['type']}: {anomaly}")
        
        # In production, send email, Slack message, etc.

