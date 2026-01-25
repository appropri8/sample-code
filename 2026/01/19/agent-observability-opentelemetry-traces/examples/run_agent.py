"""Example: Run agent and generate traces."""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.agent import run_agent, trace
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
import json


def export_traces_to_json(filepath: str):
    """Export current traces to JSON format."""
    # This is a simplified exporter - in production, use proper OTel exporters
    # For demo purposes, we'll use the console exporter and parse output
    # Or use a file-based exporter
    
    # Get spans from tracer provider
    tracer_provider = trace.get_tracer_provider()
    
    # Force flush to ensure all spans are exported
    tracer_provider.force_flush()
    
    print(f"\nTraces have been exported. Check console output or OTLP endpoint.")
    print(f"For production, configure OTLP exporter to write to {filepath}")


if __name__ == "__main__":
    # Run a few agent tasks
    tasks = [
        "Analyze the code in src/main.py",
        "Extract data from the document",
        "Read and summarize the file",
    ]
    
    print("Running agent tasks...")
    results = []
    
    for task in tasks:
        print(f"\n--- Running task: {task} ---")
        result = run_agent(
            task=task,
            user_id="user-123",
            workspace_id="workspace-456"
        )
        results.append(result)
        print(f"Result: {result}")
    
    # Flush spans
    trace.get_tracer_provider().force_flush()
    
    print("\n" + "=" * 60)
    print("Agent runs completed. Traces exported.")
    print("=" * 60)
    print("\nTo evaluate traces:")
    print("1. Configure OTLP exporter to write traces to JSON")
    print("2. Run: python src/eval_from_traces.py traces.json")
    print("\nOr use the OTel Collector with the provided config:")
    print("  otelcol --config=otel-collector-config.yaml")
