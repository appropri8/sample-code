"""
Minimal OpenTelemetry spans for agent steps and tool calls.

Span names: agent.run, agent.step, tool.call, tool.result.
Use with your existing OTLP exporter; this module only shows the pattern.
"""

try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

    trace.set_tracer_provider(TracerProvider())
    trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
    tracer = trace.get_tracer(__name__, "1.0.0")
except ImportError:
    tracer = None


def run_agent_with_spans(version: str, steps: list, execute_tool):
    """
    Run agent steps with OpenTelemetry spans: agent.run, agent.step, tool.call, tool.result.
    steps: list of (tool_name, tool_args). execute_tool(name, args) -> result dict.
    """
    if tracer is None:
        for name, args in steps:
            execute_tool(name, args)
        return

    with tracer.start_as_current_span("agent.run") as run_span:
        run_span.set_attribute("agent.version", version)
        for i, (tool_name, tool_args) in enumerate(steps):
            with tracer.start_as_current_span("agent.step") as step_span:
                step_span.set_attribute("step.index", i)
                with tracer.start_as_current_span("tool.call") as call_span:
                    call_span.set_attribute("tool.name", tool_name)
                    result = execute_tool(tool_name, tool_args)
                with tracer.start_as_current_span("tool.result") as result_span:
                    result_span.set_attribute("tool.success", result.get("success", True))
