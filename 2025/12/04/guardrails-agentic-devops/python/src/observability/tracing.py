"""
OpenTelemetry tracing for agent actions.
Provides structured traces for all agent tool calls and decisions.
"""

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from typing import Dict, Any, Optional
import json


# Setup tracer provider
def setup_tracer(service_name: str = "ops-agent", service_version: str = "1.0.0", otlp_endpoint: Optional[str] = None):
    """
    Setup OpenTelemetry tracer.
    
    Args:
        service_name: Name of the service
        service_version: Version of the service
        otlp_endpoint: OTLP endpoint (e.g., "http://jaeger:4317")
                       If None, uses console exporter
    """
    resource = Resource.create({
        "service.name": service_name,
        "service.version": service_version
    })
    
    tracer_provider = TracerProvider(resource=resource)
    
    if otlp_endpoint:
        # Use OTLP exporter (e.g., for Jaeger, Tempo)
        span_processor = BatchSpanProcessor(
            OTLPSpanExporter(endpoint=otlp_endpoint)
        )
    else:
        # Use console exporter for development
        span_processor = BatchSpanProcessor(ConsoleSpanExporter())
    
    tracer_provider.add_span_processor(span_processor)
    trace.set_tracer_provider(tracer_provider)
    
    return trace.get_tracer(__name__)


# Global tracer (will be initialized by setup_tracer)
_tracer = None


def get_tracer():
    """Get the global tracer instance."""
    global _tracer
    if _tracer is None:
        _tracer = trace.get_tracer(__name__)
    return _tracer


def trace_tool_call(
    tool_name: str,
    parameters: Dict[str, Any],
    context: Dict[str, Any],
    execute_func: callable
) -> Any:
    """
    Create OpenTelemetry span for tool call.
    
    Args:
        tool_name: Name of the tool being called
        parameters: Parameters for the tool
        context: Context including agent info, environment, etc.
        execute_func: Function to execute the tool call
    
    Returns:
        Result from execute_func
    """
    tracer = get_tracer()
    
    with tracer.start_as_current_span("tool_call") as span:
        # Set standard attributes
        span.set_attribute("tool.name", tool_name)
        span.set_attribute("tool.parameters", json.dumps(parameters))
        span.set_attribute("agent.name", context.get("agent_name", "unknown"))
        span.set_attribute("agent.role", context.get("agent_role", "unknown"))
        span.set_attribute("environment", context.get("environment", "unknown"))
        span.set_attribute("trace_id", context.get("trace_id", "unknown"))
        
        if context.get("user_id"):
            span.set_attribute("user_id", context["user_id"])
        
        # Link to related resources
        if context.get("incident_id"):
            span.set_attribute("incident.id", context["incident_id"])
        if context.get("ticket_id"):
            span.set_attribute("ticket.id", context["ticket_id"])
        
        try:
            result = execute_func()
            span.set_attribute("tool.success", True)
            span.set_attribute("tool.result", json.dumps(result) if isinstance(result, dict) else str(result))
            return result
        
        except Exception as e:
            span.set_attribute("tool.success", False)
            span.set_attribute("tool.error", str(e))
            span.record_exception(e)
            raise


# Example usage
if __name__ == "__main__":
    # Setup tracer (in production, use OTLP endpoint)
    setup_tracer(otlp_endpoint=None)  # None = console exporter
    
    # Example tool execution with tracing
    def scale_deployment(namespace: str, deployment: str, replicas: int):
        """Simulate scaling a deployment."""
        print(f"Scaling {namespace}/{deployment} to {replicas} replicas")
        return {"replicas": replicas, "status": "scaled"}
    
    context = {
        "agent_name": "ops-agent-v3",
        "agent_role": "operator",
        "environment": "production",
        "trace_id": "abc123",
        "user_id": "user-456"
    }
    
    result = trace_tool_call(
        tool_name="scale_deployment",
        parameters={
            "namespace": "production",
            "deployment": "api",
            "replicas": 10
        },
        context=context,
        execute_func=lambda: scale_deployment("production", "api", 10)
    )
    
    print(f"Result: {result}")
