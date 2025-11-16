"""Basic usage example of failure-first agent."""

import asyncio
import logging
from src.agent import FailureFirstAgent, ToolConfig
from src.fallback_chain import PrimaryTool, ReadOnlyTool, ToolWithFallback

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Run basic agent example."""
    # Configure tools
    tool_configs = {
        "search": ToolConfig(
            name="search",
            timeout=10.0,
            max_retries=3,
            requires_approval=False
        ),
        "update": ToolConfig(
            name="update",
            timeout=5.0,
            max_retries=2,
            requires_approval=True  # Updates need approval
        )
    }
    
    # Create agent
    agent = FailureFirstAgent(
        tool_configs=tool_configs,
        workflow_timeout=300.0,
        escalation_threshold=3
    )
    
    # Create tools with fallback
    search_primary = PrimaryTool("search_api", simulate_failure=False)
    search_readonly = ReadOnlyTool("search_api")
    search_tool = ToolWithFallback(
        primary_tool=search_primary,
        fallback_tools=[search_readonly]
    )
    agent.register_tool("search", search_tool)
    
    # Define plan
    plan = [
        {"tool": "search", "params": {"query": "test query"}},
        {"tool": "update", "params": {"record_id": "123", "data": {"status": "active"}}}
    ]
    
    # Run agent
    logger.info("Running agent workflow...")
    result = await agent.run("Process this record", plan)
    
    print("\n=== Agent Result ===")
    print(f"Status: {result.get('status')}")
    print(f"Steps executed: {result.get('steps_executed', 0)}")
    
    if result.get('status') == 'completed':
        print("Workflow completed successfully!")
    elif result.get('status') == 'escalated':
        print(f"Escalated to human: {result.get('ticket_id')}")
    elif result.get('status') == 'timeout':
        print(f"Workflow timed out: {result.get('message')}")
    else:
        print(f"Workflow failed: {result.get('error')}")


if __name__ == "__main__":
    asyncio.run(main())

