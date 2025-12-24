"""Tool agent that calls external tools."""
from src.agents.base_agent import BaseAgent
from opentelemetry import trace
from typing import Dict, Any
import time


class ToolAgent(BaseAgent):
    """Agent that executes tool calls."""
    
    def __init__(self, name: str, role: str, tracer, search_tool):
        super().__init__(name, role, tracer)
        self.search_tool = search_tool
    
    def _do_process(self, message: Dict[str, Any]) -> Dict[str, Any]:
        plan = message.get("plan", {})
        steps = plan.get("steps", [])
        
        tool_step = next((s for s in steps if s.get("agent") == "tool-agent"), None)
        if not tool_step:
            return message
        
        # Extract trace context for tool call
        traceparent = message.get("traceparent", "")
        
        # Call tool with retries
        max_retries = 3
        result = None
        for attempt in range(max_retries):
            with self.tracer.start_as_current_span(
                f"tool-agent.retry.{attempt + 1}"
            ) as retry_span:
                retry_span.set_attribute("retry.attempt", attempt + 1)
                retry_span.set_attribute("retry.max_attempts", max_retries)
                
                try:
                    result = self.search_tool.call(
                        {"query": tool_step.get("query", "")},
                        traceparent=traceparent
                    )
                    retry_span.set_attribute("retry.success", True)
                    break
                except Exception as e:
                    retry_span.set_attribute("retry.success", False)
                    retry_span.set_attribute("retry.error", str(e))
                    if attempt == max_retries - 1:
                        raise
                    time.sleep(0.1 * (attempt + 1))
        
        message["tool_result"] = result
        return message

