"""Search tool implementation."""
from src.tools.base_tool import BaseTool
from typing import Dict, Any
import random
import time


class SearchTool(BaseTool):
    """Mock search tool that simulates API calls."""
    
    def _do_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        query = params.get("query", "")
        
        # Simulate API call with random failures
        time.sleep(0.1)  # Simulate network latency
        
        # Randomly fail on first attempt to demonstrate retries
        if random.random() < 0.3:  # 30% failure rate
            raise Exception("API timeout")
        
        # Return mock results
        return {
            "status": "success",
            "data": f"Search results for: {query}",
            "results_count": 10
        }

