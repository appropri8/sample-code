"""PEP (Policy Enforcement Point) middleware.

Intercepts tool calls, extracts context, calls PDP, applies constraints.
"""
from typing import Dict, Any, Optional
import time


class PEPMiddleware:
    """Policy Enforcement Point middleware."""
    
    def __init__(self, pdp_client, audit_logger, cache=None):
        """Initialize PEP middleware.
        
        Args:
            pdp_client: PDP client for policy evaluation
            audit_logger: Audit logger for decision logging
            cache: Optional decision cache
        """
        self.pdp_client = pdp_client
        self.audit_logger = audit_logger
        self.cache = cache
    
    def enforce(self, request: Dict[str, Any], trace_id: str) -> Dict[str, Any]:
        """Enforce policy on a tool call request.
        
        Args:
            request: Tool call request with identity and tool_call
            trace_id: Trace ID for correlation
            
        Returns:
            Constrained request with policy constraints applied
            
        Raises:
            PermissionError: If policy denies the request
        """
        # Extract context
        context = self._extract_context(request)
        
        # Check cache first
        if self.cache:
            cache_key = self._make_cache_key(context)
            cached_decision = self.cache.get(cache_key)
            if cached_decision:
                decision = cached_decision
            else:
                decision = self.pdp_client.evaluate(context)
                self.cache.set(cache_key, decision)
        else:
            decision = self.pdp_client.evaluate(context)
        
        # Log decision
        self.audit_logger.log_decision(
            trace_id=trace_id,
            request=request,
            context=context,
            decision=decision
        )
        
        # Check decision
        if decision["decision"] == "deny":
            raise PermissionError(
                f"Policy denied: {decision.get('reason', 'No reason provided')}"
            )
        
        # Apply constraints
        constrained_request = self._apply_constraints(
            request,
            decision.get("constraints", {})
        )
        
        return constrained_request
    
    def _extract_context(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Extract policy context from request.
        
        Args:
            request: Tool call request
            
        Returns:
            Policy context dictionary
        """
        identity = request.get("identity", {})
        tool_call = request.get("tool_call", {})
        
        return {
            "subject": {
                "user_id": identity.get("user_id"),
                "tenant_id": identity.get("tenant_id"),
                "roles": identity.get("roles", []),
                "risk_tier": identity.get("risk_tier", "medium")
            },
            "action": {
                "action_type": "tool.invoke",
                "tool_name": tool_call.get("tool_name"),
                "operation": tool_call.get("action")
            },
            "resource": {
                "tool_name": tool_call.get("tool_name"),
                "dataset": tool_call.get("params", {}).get("dataset"),
                "tenant_id": tool_call.get("params", {}).get("tenant_id")
            },
            "context": {
                "time": int(time.time()),
                "ip": request.get("ip", "unknown"),
                "session_confidence": identity.get("session_confidence", 1.0),
                "prompt_risk_score": request.get("prompt_risk_score", 0.0)
            }
        }
    
    def _apply_constraints(
        self,
        request: Dict[str, Any],
        constraints: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply policy constraints to request.
        
        Args:
            request: Original request
            constraints: Policy constraints
            
        Returns:
            Request with constraints applied
        """
        constrained = request.copy()
        tool_call = constrained.get("tool_call", {})
        params = tool_call.get("params", {})
        
        # Apply row limit
        if "row_limit" in constraints:
            current_limit = params.get("limit")
            if current_limit is None:
                current_limit = float("inf")
            params["limit"] = min(current_limit, constraints["row_limit"])
        
        # Store field masking for tool to apply
        if "field_masking" in constraints:
            params["_mask_fields"] = constraints["field_masking"]
        
        # Check approval requirement
        if constraints.get("approval_required", False):
            # In production, this would trigger an approval workflow
            raise PermissionError("Approval required for this action")
        
        # Check time window
        if "time_window" in constraints:
            current_hour = time.localtime().tm_hour
            window = constraints["time_window"]
            # Simple time window check (format: "09:00-17:00")
            if "-" in window:
                start, end = window.split("-")
                start_hour = int(start.split(":")[0])
                end_hour = int(end.split(":")[0])
                if not (start_hour <= current_hour < end_hour):
                    raise PermissionError(
                        f"Action not allowed outside time window {window}"
                    )
        
        tool_call["params"] = params
        constrained["tool_call"] = tool_call
        
        return constrained
    
    def _make_cache_key(self, context: Dict[str, Any]) -> str:
        """Create cache key from context.
        
        Args:
            context: Policy context
            
        Returns:
            Cache key string
        """
        # Cache key should include: user, tenant, tool, operation
        # But NOT dynamic params (like order_id)
        return (
            f"{context['subject']['user_id']}:"
            f"{context['subject']['tenant_id']}:"
            f"{context['action']['tool_name']}:"
            f"{context['action']['operation']}"
        )

