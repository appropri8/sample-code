"""Structured logging for agents and workflows"""
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import uuid


class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logs"""
    
    def format(self, record):
        if isinstance(record.msg, dict):
            return json.dumps(record.msg)
        return super().format(record)


class AgentLogger:
    """Structured logger for agent operations"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        # JSON formatter
        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
        self.logger.addHandler(handler)
    
    def log_tool_call(
        self,
        trace_id: str,
        agent_version: str,
        tool_name: str,
        input: Dict[str, Any],
        output: Dict[str, Any],
        latency_ms: int,
        success: bool,
        error: Optional[str] = None
    ):
        """Log tool call with standardized fields"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "trace_id": trace_id,
            "agent_version": agent_version,
            "event_type": "tool_call",
            "tool_name": tool_name,
            "input": input,
            "output": output,
            "latency_ms": latency_ms,
            "success": success
        }
        
        if error:
            log_entry["error"] = error
        
        self.logger.info(json.dumps(log_entry))
    
    def log_workflow_step(
        self,
        trace_id: str,
        workflow_version: str,
        step_name: str,
        state: Dict[str, Any],
        latency_ms: int
    ):
        """Log workflow step"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "trace_id": trace_id,
            "workflow_version": workflow_version,
            "event_type": "workflow_step",
            "step_name": step_name,
            "state": state,
            "latency_ms": latency_ms
        }
        
        self.logger.info(json.dumps(log_entry))
    
    def log_agent_execution(
        self,
        trace_id: str,
        agent_version: str,
        input: Dict[str, Any],
        output: Dict[str, Any],
        latency_ms: int,
        success: bool,
        tokens_used: Optional[int] = None,
        cost: Optional[float] = None
    ):
        """Log agent execution"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "trace_id": trace_id,
            "agent_version": agent_version,
            "event_type": "agent_execution",
            "input": input,
            "output": output,
            "latency_ms": latency_ms,
            "success": success
        }
        
        if tokens_used is not None:
            log_entry["tokens_used"] = tokens_used
        if cost is not None:
            log_entry["cost"] = cost
        
        self.logger.info(json.dumps(log_entry))


def generate_trace_id() -> str:
    """Generate unique trace ID"""
    return str(uuid.uuid4())

