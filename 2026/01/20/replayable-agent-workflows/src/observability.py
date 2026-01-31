"""OpenTelemetry instrumentation for agent runs."""
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, BatchSpanProcessor
from typing import Dict, Any, Callable


# Setup tracer
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

# Add console exporter for demo
span_processor = BatchSpanProcessor(ConsoleSpanExporter())
trace.get_tracer_provider().add_span_processor(span_processor)


# GenAI semantic conventions
GENAI_SYSTEM = "gen_ai.system"
GENAI_REQUEST_MODEL = "gen_ai.request.model"
GENAI_REQUEST_TEMPERATURE = "gen_ai.request.temperature"
GENAI_REQUEST_MAX_TOKENS = "gen_ai.request.max_tokens"
GENAI_RESPONSE_FINISH_REASON = "gen_ai.response.finish_reasons"
GENAI_USAGE_INPUT_TOKENS = "gen_ai.usage.input_tokens"
GENAI_USAGE_OUTPUT_TOKENS = "gen_ai.usage.output_tokens"


def trace_agent_run(run_id: str, query: str):
    """Create a trace for an agent run."""
    return tracer.start_as_current_span(
        "agent_run",
        attributes={
            "run_id": run_id,
            "query": query
        }
    )


def trace_step(step_number: int, tool_name: str):
    """Create a span for an agent step."""
    return tracer.start_as_current_span(
        f"step_{step_number}",
        attributes={
            "step_number": step_number,
            "tool_name": tool_name
        }
    )


def trace_tool_call(tool_name: str, args: Dict[str, Any]):
    """Create a span for a tool call."""
    return tracer.start_as_current_span(
        f"tool_{tool_name}",
        attributes={
            "tool_name": tool_name,
            "args": str(args)
        }
    )


def instrument_tool(tool_func: Callable) -> Callable:
    """Instrument a tool function with tracing."""
    def wrapped(*args, **kwargs):
        with tracer.start_as_current_span(f"tool_{tool_func.__name__}") as span:
            span.set_attribute("tool_name", tool_func.__name__)
            span.set_attribute("args", str({"args": args, "kwargs": kwargs}))
            
            try:
                result = tool_func(*args, **kwargs)
                span.set_attribute("success", True)
                span.set_attribute("result_size", len(str(result)))
                return result
            except Exception as e:
                span.set_attribute("success", False)
                span.set_attribute("error", str(e))
                span.record_exception(e)
                raise
    
    return wrapped


def trace_llm_call(prompt: str, model: str, temperature: float):
    """Trace an LLM call with GenAI semantic conventions."""
    with tracer.start_as_current_span("llm_call") as span:
        span.set_attribute(GENAI_SYSTEM, "openai")
        span.set_attribute(GENAI_REQUEST_MODEL, model)
        span.set_attribute(GENAI_REQUEST_TEMPERATURE, temperature)
        span.set_attribute(GENAI_REQUEST_MAX_TOKENS, 1000)
        
        # Simulate LLM call
        response = {"text": "Generated response", "finish_reason": "stop"}
        
        span.set_attribute(GENAI_RESPONSE_FINISH_REASON, response["finish_reason"])
        span.set_attribute(GENAI_USAGE_INPUT_TOKENS, len(prompt.split()))
        span.set_attribute(GENAI_USAGE_OUTPUT_TOKENS, len(response["text"].split()))
        
        return response["text"]
