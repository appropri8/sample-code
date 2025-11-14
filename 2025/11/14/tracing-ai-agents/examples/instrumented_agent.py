"""Example of an instrumented agent loop with tracing"""

from typing import List, Dict, Any
from src.tracer import Tracer, FileBackend
from src.agent_run import AgentRun


def call_tool(tool_name: str, tool_input: Dict[str, Any], tools: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Simulate calling a tool"""
    tool = next((t for t in tools if t["name"] == tool_name), None)
    if not tool:
        raise ValueError(f"Tool {tool_name} not found")
    
    # Simulate tool execution
    if tool_name == "search":
        return {"results": ["result1", "result2", "result3"]}
    elif tool_name == "format":
        return {"formatted": f"Formatted: {tool_input.get('data', '')}"}
    elif tool_name == "calculate":
        return {"result": 42}
    else:
        return {"output": "tool output"}


def run_agent_with_tracing(
    user_input: str,
    tools: List[Dict[str, Any]],
    tracer: Tracer,
    max_steps: int = 10
) -> str:
    """Run an agent with tracing enabled"""
    
    # Start run
    run_id = tracer.start_run({
        "user_input": user_input,
        "tools": [t["name"] for t in tools],
        "model": "gpt-4"
    })
    
    try:
        messages = [
            {"role": "system", "content": "You are a helpful assistant. Use tools when needed."},
            {"role": "user", "content": user_input}
        ]
        
        step_id = 0
        
        while step_id < max_steps:
            # Simulate agent decision (in real code, call your LLM here)
            # For demo, we'll use a simple pattern based on step
            if step_id == 0:
                tool_name = "search"
                tool_input = {"query": user_input}
            elif step_id == 1:
                tool_name = "format"
                tool_input = {"data": "search results"}
            else:
                break  # Done
            
            # Simulate tool call
            tool_output = call_tool(tool_name, tool_input, tools)
            
            # Log step
            step_id += 1
            tracer.log_step(run_id, {
                "step_id": step_id,
                "tool_name": tool_name,
                "tool_input": tool_input,
                "tool_output": tool_output,
                "messages_at_step": messages.copy()
            })
            
            # Update messages
            messages.append({
                "role": "assistant",
                "content": f"I'll use {tool_name} to help you."
            })
            messages.append({
                "role": "tool",
                "content": str(tool_output)
            })
            
            # Check if done
            if step_id >= 2:
                break
        
        # Format final answer
        final_output = f"Based on the search and formatting, here's your answer: {user_input}"
        
        tracer.end_run(run_id, final_output)
        return final_output
        
    except Exception as e:
        tracer.log_error(run_id, str(e))
        raise


def main():
    """Example usage"""
    # Create tracer with file backend
    tracer = Tracer(backend=FileBackend("traces.json"))
    
    # Define available tools
    tools = [
        {"name": "search", "description": "Search for information"},
        {"name": "format", "description": "Format data"},
        {"name": "calculate", "description": "Perform calculations"}
    ]
    
    # Run agent with tracing
    result = run_agent_with_tracing(
        "What is the weather today?",
        tools,
        tracer
    )
    
    print(f"Result: {result}")
    print(f"Trace saved to traces.json")
    
    # Get the run to verify
    runs = tracer.backend.get_all_runs()
    if runs:
        run_id = list(runs.keys())[0]
        run = tracer.get_run(run_id)
        print(f"\nRun ID: {run.run_id}")
        print(f"Status: {run.status}")
        print(f"Steps: {len(run.steps)}")
        for step in run.steps:
            print(f"  Step {step.step_id}: {step.tool_name}")


if __name__ == "__main__":
    main()

