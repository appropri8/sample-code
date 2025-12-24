"""Example: Run a multi-agent workflow with tracing."""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.tracing.setup import setup_tracing
from src.agents.planner_agent import PlannerAgent
from src.agents.tool_agent import ToolAgent
from src.agents.verifier_agent import VerifierAgent
from src.agents.summarizer_agent import SummarizerAgent
from src.mesh.router import MeshRouter
from src.tools.search_tool import SearchTool
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator


def main():
    """Run the example workflow."""
    print("Setting up OpenTelemetry tracing...")
    tracer = setup_tracing("multi-agent-mesh")
    
    print("Creating tools...")
    search_tool = SearchTool("search-api", "http", tracer)
    
    print("Creating agents...")
    planner = PlannerAgent("planner-agent", "planner", tracer)
    tool_agent = ToolAgent("tool-agent", "tool-executor", tracer, search_tool)
    verifier = VerifierAgent("verifier-agent", "verifier", tracer)
    summarizer = SummarizerAgent("summarizer-agent", "summarizer", tracer)
    
    agents = {
        "planner-agent": planner,
        "tool-agent": tool_agent,
        "verifier-agent": verifier,
        "summarizer-agent": summarizer
    }
    
    print("Creating mesh router...")
    router = MeshRouter(agents, tracer)
    
    print("\nStarting workflow...")
    # Create user request with root span
    with tracer.start_as_current_span("user-request") as root_span:
        root_span.set_attribute("user.id", "user-123")
        root_span.set_attribute("request.type", "search")
        
        message = {
            "request": "Find information about Python",
            "conversation_id": "conv-abc-123",
            "workflow_id": "workflow-xyz-789"
        }
        
        # Inject trace context
        carrier = {}
        TraceContextTextMapPropagator().inject(carrier)
        message["traceparent"] = carrier.get("traceparent", "")
        
        print(f"Trace ID: {carrier.get('traceparent', 'N/A')}")
        
        # Route through agents
        result = router.route(message, [
            "planner-agent",
            "tool-agent",
            "verifier-agent",
            "summarizer-agent"
        ])
        
        print(f"\nResult: {result.get('formatted_output', 'No output')}")
        print("\nCheck Jaeger UI at http://localhost:16686 to see the trace!")


if __name__ == "__main__":
    main()

