"""Base agent class with OpenTelemetry tracing."""
from opentelemetry import trace
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from typing import Dict, Any, Optional
import os


class BaseAgent:
    """Base class for all agents with built-in tracing."""
    
    def __init__(self, name: str, role: str, tracer):
        self.name = name
        self.role = role
        self.tracer = tracer
        self.debug_mode = os.getenv("OTEL_DEBUG", "false").lower() == "true"
    
    def extract_trace_context(self, message: Dict[str, Any]) -> Optional[Any]:
        """Extract trace context from message envelope."""
        traceparent = message.get("traceparent")
        if not traceparent:
            return None
        
        carrier = {"traceparent": traceparent}
        return TraceContextTextMapPropagator().extract(carrier)
    
    def inject_trace_context(self, context: Any) -> str:
        """Inject trace context into message envelope."""
        carrier = {}
        TraceContextTextMapPropagator().inject(carrier, context)
        return carrier.get("traceparent", "")
    
    def process(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Process a message with tracing."""
        # Extract trace context
        parent_context = self.extract_trace_context(message)
        
        # Start span
        with self.tracer.start_as_current_span(
            f"agent.{self.name}.process",
            context=parent_context
        ) as span:
            # Set agent attributes
            span.set_attribute("agent.name", self.name)
            span.set_attribute("agent.role", self.role)
            span.set_attribute("conversation.id", message.get("conversation_id", ""))
            span.set_attribute("workflow.id", message.get("workflow_id", ""))
            
            # Process the message
            result = self._do_process(message)
            
            # Inject trace context into result
            current_context = trace.context_api.get_current()
            traceparent = self.inject_trace_context(current_context)
            result["traceparent"] = traceparent
            
            return result
    
    def _do_process(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Subclasses implement this."""
        raise NotImplementedError

