"""Example of fallback chain patterns."""

import asyncio
import logging
from src.fallback_chain import (
    PrimaryTool,
    CachedTool,
    ReadOnlyTool,
    ToolWithFallback,
    ToolError
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Run fallback chain examples."""
    print("=== Example 1: Primary Tool Success ===\n")
    
    # Primary tool works
    primary = PrimaryTool("search_api", simulate_failure=False)
    cached = CachedTool("search_api", cache={})
    readonly = ReadOnlyTool("search_api")
    
    tool = ToolWithFallback(
        primary_tool=primary,
        fallback_tools=[cached, readonly]
    )
    
    result = await tool.call({"query": "test"})
    print(f"Result: {result}\n")
    print(f"Fallback used: {tool.fallback_used}\n")
    
    print("=== Example 2: Primary Fails, Use Cache ===\n")
    
    # Primary fails, use cache
    primary_fail = PrimaryTool("search_api", simulate_failure=True)
    cache_with_data = CachedTool("search_api", cache={
        "()": "Cached search result"
    })
    
    tool2 = ToolWithFallback(
        primary_tool=primary_fail,
        fallback_tools=[cache_with_data, readonly]
    )
    
    result = await tool2.call({})
    print(f"Result: {result}\n")
    print(f"Fallback used: {tool2.fallback_used}\n")
    
    print("=== Example 3: All Fail, Use Read-Only ===\n")
    
    # All fail except read-only
    primary_fail2 = PrimaryTool("search_api", simulate_failure=True)
    cache_empty = CachedTool("search_api", cache={})
    readonly_works = ReadOnlyTool("search_api")
    
    tool3 = ToolWithFallback(
        primary_tool=primary_fail2,
        fallback_tools=[cache_empty, readonly_works]
    )
    
    result = await tool3.call({"query": "test"})
    print(f"Result: {result}\n")
    print(f"Fallback used: {tool3.fallback_used}\n")
    
    print("=== Example 4: All Tools Fail ===\n")
    
    # All tools fail
    primary_fail3 = PrimaryTool("search_api", simulate_failure=True)
    cache_empty2 = CachedTool("search_api", cache={})
    
    # Create a failing read-only tool
    class FailingReadOnly(ReadOnlyTool):
        async def call(self, params):
            raise ToolError("Read-only also failed")
    
    failing_readonly = FailingReadOnly("search_api")
    
    tool4 = ToolWithFallback(
        primary_tool=primary_fail3,
        fallback_tools=[cache_empty2, failing_readonly]
    )
    
    try:
        result = await tool4.call({})
        print(f"Result: {result}\n")
    except ToolError as e:
        print(f"All tools failed: {e}\n")


if __name__ == "__main__":
    asyncio.run(main())

