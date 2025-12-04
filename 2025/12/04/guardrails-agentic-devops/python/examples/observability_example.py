"""
Example: Using OpenTelemetry tracing for agent actions.
"""

from src.observability import setup_tracer, trace_tool_call


def scale_deployment(namespace: str, deployment: str, replicas: int):
    """Simulate scaling a deployment."""
    print(f"Scaling {namespace}/{deployment} to {replicas} replicas")
    return {"replicas": replicas, "status": "scaled"}


def get_pod_metrics(namespace: str, pod_name: str):
    """Simulate getting pod metrics."""
    print(f"Getting metrics for {namespace}/{pod_name}")
    return {"cpu": "50%", "memory": "60%"}


def main():
    # Setup tracer
    # In production, use OTLP endpoint: setup_tracer(otlp_endpoint="http://jaeger:4317")
    # For this example, we'll use console exporter
    setup_tracer(
        service_name="ops-agent",
        service_version="1.0.0",
        otlp_endpoint=None  # None = console exporter for development
    )
    
    print("Observability Example: Tracing Agent Actions")
    print("=" * 50)
    print()
    
    # Example 1: Trace a tool call
    print("Example 1: Tracing scale_deployment call")
    context = {
        "agent_name": "ops-agent-v3",
        "agent_role": "operator",
        "environment": "production",
        "trace_id": "abc123",
        "user_id": "user-456",
        "incident_id": "inc-789"
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
    print()
    
    # Example 2: Trace another tool call
    print("Example 2: Tracing get_pod_metrics call")
    context2 = {
        "agent_name": "observer-agent",
        "agent_role": "observer",
        "environment": "production",
        "trace_id": "def456"
    }
    
    result2 = trace_tool_call(
        tool_name="get_pod_metrics",
        parameters={
            "namespace": "production",
            "pod_name": "api-pod-123"
        },
        context=context2,
        execute_func=lambda: get_pod_metrics("production", "api-pod-123")
    )
    
    print(f"Result: {result2}")
    print()
    
    print("Note: In production, traces would be sent to your observability backend")
    print("(Jaeger, Tempo, etc.) and be queryable via trace_id.")


if __name__ == "__main__":
    main()
