"""Audit logger for policy decisions."""
from typing import Dict, Any
import time


class AuditLogger:
    """Audit logger for policy decisions."""
    
    def __init__(self, log_store):
        """Initialize audit logger.
        
        Args:
            log_store: Log store implementation (e.g., MemoryLogStore)
        """
        self.log_store = log_store
    
    def log_decision(
        self,
        trace_id: str,
        request: Dict[str, Any],
        context: Dict[str, Any],
        decision: Dict[str, Any]
    ):
        """Log a policy decision for audit.
        
        Args:
            trace_id: Trace ID for correlation with OpenTelemetry traces
            request: Original request
            context: Policy context
            decision: Policy decision
        """
        log_entry = {
            "timestamp": int(time.time()),
            "trace_id": trace_id,
            "decision": decision["decision"],
            "policy_id": decision.get("policy_id"),
            "reason": decision.get("reason"),
            "subject": {
                "user_id": context["subject"]["user_id"],
                "tenant_id": context["subject"]["tenant_id"],
                "roles": context["subject"]["roles"]
            },
            "action": {
                "tool_name": context["action"]["tool_name"],
                "operation": context["action"]["operation"]
            },
            "resource": {
                "dataset": context["resource"].get("dataset"),
                "tenant_id": context["resource"].get("tenant_id")
            },
            "constraints": decision.get("constraints", {}),
            "request_id": request.get("policy_context", {}).get("request_id")
        }
        
        self.log_store.write(log_entry)
    
    def log_break_glass_activation(
        self,
        session_id: str,
        user_id: str,
        reason: str
    ):
        """Log break-glass mode activation.
        
        Args:
            session_id: Break-glass session ID
            user_id: User who activated break-glass
            reason: Reason for activation
        """
        log_entry = {
            "timestamp": int(time.time()),
            "event": "break_glass_activated",
            "session_id": session_id,
            "user_id": user_id,
            "reason": reason
        }
        
        self.log_store.write(log_entry)

