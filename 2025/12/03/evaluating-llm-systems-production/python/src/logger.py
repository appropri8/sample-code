"""
Logging module for LLM calls.
Captures input, output, metadata, and performance metrics.
"""

import json
import hashlib
import re
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict


def redact_pii(text: str) -> str:
    """Redact PII from text."""
    # Email addresses
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', text)
    # Phone numbers
    text = re.sub(r'\b\d{3}-\d{3}-\d{4}\b', '[PHONE]', text)
    # Credit cards
    text = re.sub(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b', '[CARD]', text)
    return text


def hash_user_id(user_id: str) -> str:
    """Hash user ID for privacy."""
    return hashlib.sha256(user_id.encode()).hexdigest()[:16]


@dataclass
class LLMLog:
    """Log record for a single LLM call."""
    request_id: str
    timestamp: str
    user_id_hash: str
    session_id: Optional[str] = None
    input: Optional[Dict[str, Any]] = None
    output: Optional[Dict[str, Any]] = None
    model: Optional[Dict[str, Any]] = None
    prompt: Optional[Dict[str, Any]] = None
    performance: Optional[Dict[str, Any]] = None
    experiment: Optional[Dict[str, Any]] = None
    feedback: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


class LLMLogger:
    """Logger for LLM calls."""
    
    def __init__(self, log_file: Optional[str] = None, redact_pii_enabled: bool = True):
        self.log_file = log_file
        self.redact_pii_enabled = redact_pii_enabled
        self.logs: List[LLMLog] = []
    
    def log_call(
        self,
        request_id: str,
        user_id: str,
        query: str,
        response: str,
        model_name: str,
        model_version: str,
        prompt_version: str,
        latency_ms: int,
        tokens_used: int,
        cost_usd: float,
        session_id: Optional[str] = None,
        context: Optional[List[str]] = None,
        experiment_variant: Optional[str] = None,
        experiment_cohort: Optional[str] = None,
        temperature: float = 0.7
    ) -> LLMLog:
        """Log an LLM call."""
        
        # Redact PII if enabled
        query_redacted = redact_pii(query) if self.redact_pii_enabled else query
        response_redacted = redact_pii(response) if self.redact_pii_enabled else response
        
        # Hash user ID
        user_id_hash = hash_user_id(user_id)
        
        # Create log record
        log = LLMLog(
            request_id=request_id,
            timestamp=datetime.utcnow().isoformat(),
            user_id_hash=user_id_hash,
            session_id=session_id,
            input={
                "query": query_redacted,
                "context": context or []
            },
            output={
                "text": response_redacted,
                "tokens_used": tokens_used
            },
            model={
                "name": model_name,
                "version": model_version,
                "temperature": temperature
            },
            prompt={
                "template_version": prompt_version,
                "template_hash": hashlib.md5(prompt_version.encode()).hexdigest()[:8]
            },
            performance={
                "latency_ms": latency_ms,
                "cost_usd": cost_usd
            },
            experiment={
                "variant": experiment_variant or "baseline",
                "cohort": experiment_cohort or "control"
            } if experiment_variant else None
        )
        
        # Store log
        self.logs.append(log)
        
        # Write to file if specified
        if self.log_file:
            with open(self.log_file, 'a') as f:
                f.write(log.to_json() + '\n')
        
        return log
    
    def add_feedback(
        self,
        request_id: str,
        thumbs_up: Optional[bool] = None,
        rating: Optional[int] = None,
        labels: Optional[Dict[str, str]] = None
    ):
        """Add feedback to an existing log."""
        for log in self.logs:
            if log.request_id == request_id:
                log.feedback = {
                    "thumbs_up": thumbs_up,
                    "rating": rating,
                    "labels": labels or {},
                    "timestamp": datetime.utcnow().isoformat()
                }
                break
    
    def get_logs(self, user_id_hash: Optional[str] = None, variant: Optional[str] = None) -> List[LLMLog]:
        """Get logs, optionally filtered."""
        logs = self.logs
        if user_id_hash:
            logs = [l for l in logs if l.user_id_hash == user_id_hash]
        if variant:
            logs = [l for l in logs if l.experiment and l.experiment.get("variant") == variant]
        return logs

