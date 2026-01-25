"""Instrumented agent loop with OpenTelemetry tracing."""

import json
import time
from typing import Any, Dict, Optional
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource

from .redaction import set_attribute_safe

# Setup OpenTelemetry
resource = Resource.create({
    "service.name": "agent-observability-demo",
    "service.version": "1.0.0",
})

trace.set_tracer_provider(TracerProvider(resource=resource))
tracer = trace.get_tracer(__name__)

# Add console exporter (for development)
console_exporter = ConsoleSpanExporter()
console_processor = BatchSpanProcessor(console_exporter)
trace.get_tracer_provider().add_span_processor(console_processor)

# Add OTLP exporter (for production - can be swapped)
# Uncomment and configure endpoint for production use
# otlp_exporter = OTLPSpanExporter(endpoint="http://localhost:4317")
# otlp_processor = BatchSpanProcessor(otlp_exporter)
# trace.get_tracer_provider().add_span_processor(otlp_processor)


class MockLLMResponse:
    """Mock LLM response for demo purposes."""
    
    def __init__(self, text: str, tokens: int = 100, needs_tool: bool = False, tool_name: Optional[str] = None, tool_args: Optional[Dict] = None):
        self.text = text
        self.usage = MockUsage(tokens)
        self.needs_tool = needs_tool
        self.tool_name = tool_name
        self.tool_args = tool_args or {}
        self.final_answer = text if not needs_tool else None


class MockUsage:
    """Mock token usage."""
    
    def __init__(self, total: int):
        self.prompt_tokens = total // 2
        self.completion_tokens = total // 2
        self.total_tokens = total


class MockLLMClient:
    """Mock LLM client for demo."""
    
    def generate(self, prompt: str, model: str = "gpt-4") -> MockLLMResponse:
        """Generate a mock response."""
        # Simulate latency
        time.sleep(0.1)
        
        # Simple logic: if prompt mentions "read", return tool call
        if "read" in prompt.lower() or "file" in prompt.lower():
            return MockLLMResponse(
                text="I need to read a file",
                tokens=150,
                needs_tool=True,
                tool_name="read_file",
                tool_args={"path": "src/main.py"}
            )
        return MockLLMResponse(
            text="Task completed successfully",
            tokens=100,
            needs_tool=False
        )


class MockToolExecutor:
    """Mock tool executor for demo."""
    
    def execute(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool call."""
        # Simulate latency
        time.sleep(0.05)
        
        if tool_name == "read_file":
            return {"content": f"File content from {args.get('path', 'unknown')}"}
        elif tool_name == "write_file":
            return {"success": True, "path": args.get("path")}
        else:
            raise ValueError(f"Unknown tool: {tool_name}")


# Global instances
llm_client = MockLLMClient()
tool_executor = MockToolExecutor()


def estimate_cost(model: str, usage: MockUsage) -> float:
    """Estimate cost based on model and usage."""
    # Mock pricing (GPT-4)
    if "gpt-4" in model.lower():
        return (usage.prompt_tokens * 0.03 + usage.completion_tokens * 0.06) / 1000
    return 0.001  # Default


def call_llm(prompt: str, model: str = "gpt-4"):
    """Call LLM with tracing."""
    with tracer.start_as_current_span("llm.call") as span:
        set_attribute_safe(span, "llm.model", model)
        set_attribute_safe(span, "llm.prompt_length", len(prompt))
        
        start_time = time.time()
        response = llm_client.generate(prompt, model=model)
        duration = time.time() - start_time
        
        set_attribute_safe(span, "llm.tokens_input", response.usage.prompt_tokens)
        set_attribute_safe(span, "llm.tokens_output", response.usage.completion_tokens)
        set_attribute_safe(span, "llm.tokens_total", response.usage.total_tokens)
        set_attribute_safe(span, "llm.latency_ms", int(duration * 1000))
        
        cost = estimate_cost(model, response.usage)
        set_attribute_safe(span, "llm.cost_estimate", cost)
        
        # Store full prompt/response in events (not attributes)
        span.add_event("llm.prompt", {"prompt": prompt[:500]})  # Truncate
        span.add_event("llm.response", {"response": response.text[:500]})
        
        return response


def call_tool(tool_name: str, args: Dict[str, Any]):
    """Call tool with tracing."""
    with tracer.start_as_current_span("tool.call") as span:
        set_attribute_safe(span, "tool.name", tool_name)
        set_attribute_safe(span, "tool.args_size", len(json.dumps(args)))
        
        start_time = time.time()
        try:
            result = tool_executor.execute(tool_name, args)
            duration = time.time() - start_time
            
            set_attribute_safe(span, "tool.status", "success")
            set_attribute_safe(span, "tool.latency_ms", int(duration * 1000))
            set_attribute_safe(span, "tool.result_size", len(json.dumps(result)))
            
            return result
        except Exception as e:
            duration = time.time() - start_time
            set_attribute_safe(span, "tool.status", "error")
            set_attribute_safe(span, "tool.error", str(e)[:200])  # Truncate
            set_attribute_safe(span, "tool.latency_ms", int(duration * 1000))
            span.record_exception(e)
            raise


def make_decision(context: Dict, options: list):
    """Make a decision with tracing."""
    with tracer.start_as_current_span("decision") as span:
        set_attribute_safe(span, "decision.type", "tool_selection")
        set_attribute_safe(span, "decision.options_count", len(options))
        
        # Simple decision logic
        if options:
            selected = options[0]
            set_attribute_safe(span, "decision.selected", selected)
            set_attribute_safe(span, "decision.reasoning", "First available option"[:200])
            return selected
        return None


def classify_task(task: str) -> str:
    """Classify task type."""
    if "analyze" in task.lower() or "code" in task.lower():
        return "code_analysis"
    elif "extract" in task.lower() or "data" in task.lower():
        return "data_extraction"
    return "general"


def run_agent(task: str, user_id: str = "user-123", workspace_id: str = "workspace-456", max_iterations: int = 10):
    """Run agent with full tracing.
    
    Args:
        task: Task description
        user_id: User identifier
        workspace_id: Workspace identifier
        max_iterations: Maximum number of iterations
    
    Returns:
        Result dictionary with success status and final answer
    """
    with tracer.start_as_current_span("agent.run") as root_span:
        set_attribute_safe(root_span, "agent.task", task)
        set_attribute_safe(root_span, "agent.task_type", classify_task(task))
        set_attribute_safe(root_span, "agent.user_id", user_id)
        set_attribute_safe(root_span, "agent.workspace_id", workspace_id)
        set_attribute_safe(root_span, "agent.job_id", f"job-{int(time.time())}")
        
        context = {}
        iteration = 0
        
        try:
            for i in range(max_iterations):
                iteration = i
                
                # Build prompt
                prompt = f"Task: {task}\nContext: {json.dumps(context, default=str)[:500]}"
                
                # LLM call
                response = call_llm(prompt, model="gpt-4")
                
                # Decision: should we call a tool?
                if response.needs_tool:
                    # Decision span
                    decision = make_decision(context, [response.tool_name])
                    
                    # Tool call
                    try:
                        result = call_tool(response.tool_name, response.tool_args)
                        context["last_tool_result"] = result
                        context[f"tool_call_{i}"] = {"tool": response.tool_name, "success": True}
                    except Exception as e:
                        context[f"tool_call_{i}"] = {"tool": response.tool_name, "success": False, "error": str(e)}
                        # Continue or break based on error type
                        if "timeout" in str(e).lower():
                            break
                else:
                    # Done - we have a final answer
                    set_attribute_safe(root_span, "agent.completed", True)
                    set_attribute_safe(root_span, "agent.final_state", "success")
                    set_attribute_safe(root_span, "agent.iterations", i + 1)
                    return {
                        "success": True,
                        "answer": response.final_answer or response.text,
                        "iterations": i + 1,
                    }
            
            # Max iterations reached
            set_attribute_safe(root_span, "agent.completed", False)
            set_attribute_safe(root_span, "agent.final_state", "max_iterations")
            set_attribute_safe(root_span, "agent.iterations", iteration + 1)
            return {
                "success": False,
                "answer": None,
                "error": "Max iterations reached",
                "iterations": iteration + 1,
            }
            
        except Exception as e:
            set_attribute_safe(root_span, "agent.completed", False)
            set_attribute_safe(root_span, "agent.final_state", "error")
            set_attribute_safe(root_span, "agent.error", str(e)[:200])
            root_span.record_exception(e)
            return {
                "success": False,
                "answer": None,
                "error": str(e),
                "iterations": iteration + 1,
            }


if __name__ == "__main__":
    # Example usage
    result = run_agent(
        task="Analyze the code in src/main.py",
        user_id="user-123",
        workspace_id="workspace-456"
    )
    print(f"\nAgent result: {result}")
    
    # Flush spans
    trace.get_tracer_provider().force_flush()
