"""Shadow mode implementation for running candidate agents without affecting users."""

import logging
from datetime import datetime
from typing import Dict, Any, Optional
from .agent_factory import create_agent

logger = logging.getLogger(__name__)


class ShadowModeRouter:
    """Routes requests to current agent and runs candidate in shadow mode."""
    
    def __init__(
        self,
        agent_name: str,
        current_version: str,
        candidate_version: Optional[str] = None
    ):
        self.agent_name = agent_name
        self.current_version = current_version
        self.candidate_version = candidate_version
        
        # Load agents
        self.current_agent = create_agent(agent_name, current_version)
        self.candidate_agent = None
        if candidate_version:
            self.candidate_agent = create_agent(agent_name, candidate_version)
    
    def process(self, user_message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process request with current agent, run candidate in shadow mode.
        
        Returns current agent's response.
        """
        # Process with current agent (synchronous, user-facing)
        current_response = self.current_agent.process(user_message, context)
        
        # Process with candidate agent (asynchronous, shadow mode)
        if self.candidate_agent:
            try:
                candidate_response = self.candidate_agent.process(user_message, context)
                
                # Log both responses for comparison
                self._log_comparison(
                    user_message=user_message,
                    context=context or {},
                    current_response=current_response,
                    candidate_response=candidate_response
                )
            except Exception as e:
                logger.error(f"Shadow mode error: {e}", exc_info=True)
                # Don't fail the request if shadow mode fails
        
        return current_response
    
    def _log_comparison(
        self,
        user_message: str,
        context: Dict[str, Any],
        current_response: Dict[str, Any],
        candidate_response: Dict[str, Any]
    ):
        """Log both responses for later analysis."""
        comparison = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_message": user_message,
            "context": context,
            "current_version": self.current_version,
            "candidate_version": self.candidate_version,
            "current_response": {
                "tool_calls": current_response.get("tool_calls", []),
                "response": current_response.get("response", ""),
                "cost": current_response.get("cost", 0),
                "latency_ms": current_response.get("latency_ms", 0)
            },
            "candidate_response": {
                "tool_calls": candidate_response.get("tool_calls", []),
                "response": candidate_response.get("response", ""),
                "cost": candidate_response.get("cost", 0),
                "latency_ms": candidate_response.get("latency_ms", 0)
            },
            "differences": self._compute_differences(current_response, candidate_response)
        }
        
        # Log to console (in production, log to database or logging service)
        logger.info("Shadow mode comparison", extra=comparison)
        print(f"[SHADOW MODE] Comparison logged: {comparison['differences']}")
    
    def _compute_differences(
        self,
        current: Dict[str, Any],
        candidate: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Compute differences between responses."""
        return {
            "tool_calls_different": (
                current.get("tool_calls", []) != candidate.get("tool_calls", [])
            ),
            "cost_difference": (
                candidate.get("cost", 0) - current.get("cost", 0)
            ),
            "latency_difference_ms": (
                candidate.get("latency_ms", 0) - current.get("latency_ms", 0)
            )
        }
