"""Monitoring and anomaly detection for prompt pipelines"""

import logging
import json
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from dataclasses import dataclass

from .pipeline import PromptMetadata

class AnomalyDetector:
    """Detect anomalies in prompt pipeline usage"""
    
    def __init__(self, alert_threshold: int = 5):
        """
        Initialize anomaly detector
        
        Args:
            alert_threshold: Number of suspicious patterns to trigger alert
        """
        self.alert_threshold = alert_threshold
        self.request_history = defaultdict(list)
        self.logger = logging.getLogger(__name__)
    
    def check_anomaly(
        self, 
        user_id: Optional[str],
        metadata: PromptMetadata,
        input_text: str
    ) -> Dict:
        """
        Check for anomalies and return detection results
        
        Args:
            user_id: Optional user identifier
            metadata: Request metadata
            input_text: Sanitised input text
            
        Returns:
            Dict with 'is_anomaly', 'reasons', and 'risk_score'
        """
        reasons = []
        risk_score = 0.0
        
        # Check 1: Suspicious patterns
        if metadata.suspicious_patterns:
            risk_score += len(metadata.suspicious_patterns) * 0.3
            reasons.append(f"Detected {len(metadata.suspicious_patterns)} suspicious patterns")
        
        # Check 2: Unusually long input
        if metadata.input_length > 1500:
            risk_score += 0.2
            reasons.append(f"Unusually long input: {metadata.input_length} chars")
        
        # Check 3: Rate limiting (if user_id provided)
        if user_id:
            recent_requests = [
                req for req in self.request_history[user_id]
                if req["timestamp"] > datetime.now() - timedelta(minutes=1)
            ]
            if len(recent_requests) > 10:
                risk_score += 0.3
                reasons.append(f"High request rate: {len(recent_requests)} in last minute")
        
        # Check 4: Pattern repetition
        if user_id and len(self.request_history[user_id]) > 0:
            recent_inputs = [req["input"] for req in self.request_history[user_id][-5:]]
            if len(set(recent_inputs)) == 1 and len(recent_inputs) >= 3:
                risk_score += 0.2
                reasons.append("Repeated identical inputs")
        
        # Record request
        if user_id:
            self.request_history[user_id].append({
                "timestamp": datetime.now(),
                "input": input_text[:100],  # Store truncated version
                "metadata": metadata
            })
            # Keep only last 100 requests per user
            if len(self.request_history[user_id]) > 100:
                self.request_history[user_id] = self.request_history[user_id][-100:]
        
        is_anomaly = (
            risk_score >= 0.5 or 
            len(metadata.suspicious_patterns) >= self.alert_threshold
        )
        
        if is_anomaly:
            self.logger.warning(
                f"Anomaly detected: risk_score={risk_score:.2f}, reasons={reasons}"
            )
        
        return {
            "is_anomaly": is_anomaly,
            "risk_score": risk_score,
            "reasons": reasons
        }


class PipelineMonitor:
    """Monitor pipeline for drift and exploitation"""
    
    def __init__(self):
        self.metrics = {
            "total_requests": 0,
            "suspicious_requests": 0,
            "anomaly_rate": 0.0,
            "average_risk_score": 0.0
        }
        self.logger = logging.getLogger(__name__)
    
    def update_metrics(
        self,
        has_suspicious_patterns: bool,
        anomaly_result: Optional[Dict]
    ):
        """Update monitoring metrics"""
        self.metrics["total_requests"] += 1
        
        if has_suspicious_patterns:
            self.metrics["suspicious_requests"] += 1
        
        if anomaly_result:
            risk_score = anomaly_result.get("risk_score", 0.0)
            # Update running average
            current_avg = self.metrics["average_risk_score"]
            n = self.metrics["total_requests"]
            self.metrics["average_risk_score"] = (
                (current_avg * (n - 1) + risk_score) / n
            )
        
        # Calculate anomaly rate
        self.metrics["anomaly_rate"] = (
            self.metrics["suspicious_requests"] / 
            max(self.metrics["total_requests"], 1)
        )
        
        # Alert if metrics indicate problems
        if self.metrics["anomaly_rate"] > 0.1:  # More than 10% suspicious
            self.logger.warning(
                f"High anomaly rate detected: {self.metrics['anomaly_rate']:.2%}"
            )
    
    def get_metrics(self) -> Dict:
        """Get current metrics"""
        return self.metrics.copy()


class PipelineLogger:
    """Structured logging for prompt pipeline"""
    
    def __init__(self, log_file: Optional[str] = None):
        """
        Initialize logger
        
        Args:
            log_file: Optional file path for logging
        """
        self.logger = logging.getLogger(__name__)
        self.log_file = log_file
    
    def log_request(
        self,
        user_id: Optional[str],
        input_text: str,
        metadata: PromptMetadata,
        anomaly_result: Optional[Dict] = None
    ):
        """Log request with structured data"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "request",
            "user_id": user_id,
            "input_length": metadata.input_length,
            "suspicious_patterns": metadata.suspicious_patterns,
            "anomaly_detected": anomaly_result["is_anomaly"] if anomaly_result else False,
            "risk_score": anomaly_result.get("risk_score", 0.0) if anomaly_result else 0.0
        }
        
        self.logger.info(json.dumps(log_entry))
        
        if self.log_file:
            with open(self.log_file, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        
        # Alert on high-risk requests
        if anomaly_result and anomaly_result.get("risk_score", 0) > 0.7:
            self._send_alert(log_entry)
    
    def _send_alert(self, log_entry: Dict):
        """Send alert for high-risk requests"""
        # In production, this would send to monitoring system
        self.logger.critical(f"ALERT: High-risk request detected: {log_entry}")

