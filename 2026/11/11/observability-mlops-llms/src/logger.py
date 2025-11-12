"""Observability logger for LLM calls"""

import json
import sqlite3
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass
from prometheus_client import Counter, Histogram

# Prometheus metrics
llm_requests_total = Counter(
    'llm_requests_total',
    'Total LLM requests',
    ['model', 'prompt_version', 'status']
)

llm_tokens_total = Counter(
    'llm_tokens_total',
    'Total tokens consumed',
    ['model', 'prompt_version', 'type']
)

llm_latency_seconds = Histogram(
    'llm_latency_seconds',
    'LLM request latency',
    ['model', 'prompt_version'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
)

llm_cost_usd = Counter(
    'llm_cost_usd',
    'LLM cost in USD',
    ['model', 'prompt_version']
)


@dataclass
class LLMCallLog:
    timestamp: str
    request_id: str
    prompt_version: str
    model: str
    prompt: str
    response: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    latency_ms: float
    cost_usd: float
    status: str
    error: Optional[str] = None
    metadata: Dict[str, Any] = None


class ObservabilityLogger:
    """Logger for LLM calls with database storage and Prometheus metrics"""
    
    def __init__(self, db_path: str = "observability.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize SQLite database for logging"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS llm_calls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                request_id TEXT,
                prompt_version TEXT,
                model TEXT,
                prompt TEXT,
                response TEXT,
                input_tokens INTEGER,
                output_tokens INTEGER,
                total_tokens INTEGER,
                latency_ms REAL,
                cost_usd REAL,
                status TEXT,
                error TEXT,
                metadata TEXT
            )
        """)
        conn.commit()
        conn.close()
    
    def _calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost based on model pricing (as of 2024)"""
        pricing = {
            "gpt-4": {"input": 0.03 / 1000, "output": 0.06 / 1000},
            "gpt-4-turbo": {"input": 0.01 / 1000, "output": 0.03 / 1000},
            "gpt-3.5-turbo": {"input": 0.0015 / 1000, "output": 0.002 / 1000},
        }
        model_pricing = pricing.get(model, pricing["gpt-3.5-turbo"])
        return (input_tokens * model_pricing["input"]) + (output_tokens * model_pricing["output"])
    
    def log_llm_call(
        self,
        request_id: str,
        prompt_version: str,
        model: str,
        prompt: str,
        response: str,
        usage: Dict[str, int],
        latency_ms: float,
        status: str = "success",
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> LLMCallLog:
        """Log an LLM call to database and Prometheus"""
        input_tokens = usage.get("prompt_tokens", 0)
        output_tokens = usage.get("completion_tokens", 0)
        total_tokens = usage.get("total_tokens", 0)
        cost_usd = self._calculate_cost(model, input_tokens, output_tokens)
        
        log_entry = LLMCallLog(
            timestamp=datetime.utcnow().isoformat(),
            request_id=request_id,
            prompt_version=prompt_version,
            model=model,
            prompt=prompt,
            response=response,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            latency_ms=latency_ms,
            cost_usd=cost_usd,
            status=status,
            error=error,
            metadata=metadata or {}
        )
        
        # Store in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO llm_calls (
                timestamp, request_id, prompt_version, model, prompt, response,
                input_tokens, output_tokens, total_tokens, latency_ms, cost_usd,
                status, error, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            log_entry.timestamp,
            log_entry.request_id,
            log_entry.prompt_version,
            log_entry.model,
            log_entry.prompt,
            log_entry.response,
            log_entry.input_tokens,
            log_entry.output_tokens,
            log_entry.total_tokens,
            log_entry.latency_ms,
            log_entry.cost_usd,
            log_entry.status,
            log_entry.error,
            json.dumps(log_entry.metadata)
        ))
        conn.commit()
        conn.close()
        
        # Export to Prometheus
        llm_requests_total.labels(
            model=model,
            prompt_version=prompt_version,
            status=status
        ).inc()
        
        llm_tokens_total.labels(
            model=model,
            prompt_version=prompt_version,
            type="input"
        ).inc(input_tokens)
        
        llm_tokens_total.labels(
            model=model,
            prompt_version=prompt_version,
            type="output"
        ).inc(output_tokens)
        
        llm_latency_seconds.labels(
            model=model,
            prompt_version=prompt_version
        ).observe(latency_ms / 1000.0)
        
        llm_cost_usd.labels(
            model=model,
            prompt_version=prompt_version
        ).inc(cost_usd)
        
        return log_entry

