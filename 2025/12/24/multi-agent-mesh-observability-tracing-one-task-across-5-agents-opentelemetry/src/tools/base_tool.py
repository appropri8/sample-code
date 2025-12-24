"""Base tool class with OpenTelemetry tracing."""
from opentelemetry import trace
from typing import Dict, Any, Optional
import time


class BaseTool:
    """Base class for all tools with built-in tracing."""
    
    def __init__(self, name: str, tool_type: str, tracer):
        self.name = name
        self.tool_type = tool_type
        self.tracer = tracer
    
    def call(self, params: Dict[str, Any], traceparent: Optional[str] = None) -> Dict[str, Any]:
        """Call the tool with tracing."""
        # Extract trace context if provided
        parent_context = None
        if traceparent:
            from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
            carrier = {"traceparent": traceparent}
            parent_context = TraceContextTextMapPropagator().extract(carrier)
        
        # Start span
        with self.tracer.start_as_current_span(
            f"tool.{self.name}.call",
            context=parent_context
        ) as span:
            # Set tool attributes
            span.set_attribute("tool.name", self.name)
            span.set_attribute("tool.type", self.tool_type)
            span.set_attribute("tool.target", params.get("target", ""))
            
            # Call the tool
            start_time = time.time()
            try:
                result = self._do_call(params)
                duration = (time.time() - start_time) * 1000
                
                span.set_attribute("tool.duration_ms", duration)
                span.set_attribute("tool.success", True)
                
                return result
            except Exception as e:
                duration = (time.time() - start_time) * 1000
                span.set_attribute("tool.duration_ms", duration)
                span.set_attribute("tool.success", False)
                span.set_attribute("tool.error", str(e))
                span.record_exception(e)
                raise
    
    def _do_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Subclasses implement this."""
        raise NotImplementedError

