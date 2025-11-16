"""Fallback chain implementation for tools."""

import asyncio
import logging
from typing import Callable, Any, Optional, List, Dict
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class ToolError(Exception):
    """Base exception for tool errors."""
    pass


class Tool(ABC):
    """Base class for tools."""
    
    @abstractmethod
    async def call(self, params: Dict[str, Any]) -> Any:
        """Call the tool with given parameters."""
        pass


class PrimaryTool(Tool):
    """Primary tool implementation."""
    
    def __init__(self, name: str, simulate_failure: bool = False):
        self.name = name
        self.simulate_failure = simulate_failure
    
    async def call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Call primary tool."""
        if self.simulate_failure:
            raise ToolError(f"Primary tool {self.name} failed")
        
        # Simulate API call
        await asyncio.sleep(0.1)
        return {
            "tool": self.name,
            "source": "primary",
            "data": f"Result from {self.name}",
            "params": params
        }


class CachedTool(Tool):
    """Cached fallback tool."""
    
    def __init__(self, name: str, cache: Optional[Dict] = None):
        self.name = name
        self.cache = cache or {}
    
    async def call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Call cached tool."""
        cache_key = str(sorted(params.items()))
        
        if cache_key in self.cache:
            logger.info(f"Using cached result for {self.name}")
            return {
                "tool": self.name,
                "source": "cache",
                "data": self.cache[cache_key],
                "params": params
            }
        
        raise ToolError(f"No cached result for {self.name}")


class ReadOnlyTool(Tool):
    """Read-only fallback tool."""
    
    def __init__(self, name: str):
        self.name = name
    
    async def call_readonly(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Call read-only version."""
        await asyncio.sleep(0.1)
        return {
            "tool": self.name,
            "source": "readonly",
            "data": f"Read-only result from {self.name}",
            "params": params
        }
    
    async def call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Call read-only tool."""
        return await self.call_readonly(params)


class ToolWithFallback:
    """Tool wrapper with fallback chain."""
    
    def __init__(
        self,
        primary_tool: Tool,
        fallback_tools: List[Tool],
        cache: Optional[Dict] = None
    ):
        self.primary_tool = primary_tool
        self.fallback_tools = fallback_tools
        self.cache = cache or {}
        self.fallback_used = False
    
    def _cache_key(self, params: Dict[str, Any]) -> str:
        """Generate cache key from params."""
        return str(sorted(params.items()))
    
    async def call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call tool with fallback chain.
        
        Tries primary tool first, then falls back to cached or read-only versions.
        """
        # Try primary tool
        try:
            result = await self.primary_tool.call(params)
            
            # Cache successful results
            cache_key = self._cache_key(params)
            self.cache[cache_key] = result.get("data")
            
            logger.info(f"Primary tool {self.primary_tool.name} succeeded")
            return result
        
        except ToolError as e:
            logger.warning(f"Primary tool failed: {e}, trying fallbacks")
            self.fallback_used = True
        
        # Try cache fallback
        cache_key = self._cache_key(params)
        if cache_key in self.cache:
            logger.info("Using cached result")
            return {
                "tool": self.primary_tool.name,
                "source": "cache",
                "data": self.cache[cache_key],
                "params": params
            }
        
        # Try fallback tools
        for fallback in self.fallback_tools:
            try:
                result = await fallback.call(params)
                logger.info(f"Fallback tool {fallback.name} succeeded")
                return result
            except ToolError as e:
                logger.warning(f"Fallback tool {fallback.name} failed: {e}")
                continue
        
        # All fallbacks exhausted
        raise ToolError(f"All tools failed for {self.primary_tool.name}")


class ModelFallback:
    """Model fallback implementation."""
    
    def __init__(self, primary_model: Callable, backup_model: Callable):
        self.primary_model = primary_model
        self.backup_model = backup_model
    
    def simplify_prompt(self, prompt: str) -> str:
        """Simplify prompt for backup model."""
        # Simple simplification - in production, use more sophisticated logic
        lines = prompt.split('\n')
        # Keep only first few lines
        return '\n'.join(lines[:3])
    
    async def call(self, prompt: str, context: List[str]) -> str:
        """Call model with fallback."""
        try:
            # Try primary model
            result = await self.primary_model(prompt, context)
            logger.info("Primary model succeeded")
            return result
        except Exception as e:
            logger.warning(f"Primary model failed: {e}, trying backup")
            
            # Simplify prompt for backup
            simplified_prompt = self.simplify_prompt(prompt)
            
            try:
                result = await self.backup_model(simplified_prompt, context)
                logger.info("Backup model succeeded")
                return result
            except Exception as e2:
                logger.error(f"Backup model also failed: {e2}")
                raise


# Example usage
if __name__ == "__main__":
    async def main():
        # Create tools
        primary = PrimaryTool("search_api", simulate_failure=True)
        cached = CachedTool("search_api", cache={"()": "Cached result"})
        readonly = ReadOnlyTool("search_api")
        
        # Create tool with fallback
        tool = ToolWithFallback(
            primary_tool=primary,
            fallback_tools=[cached, readonly],
            cache={"()": "Cached result"}
        )
        
        # Call tool
        try:
            result = await tool.call({})
            print(f"Result: {result}")
            print(f"Fallback used: {tool.fallback_used}")
        except ToolError as e:
            print(f"All tools failed: {e}")
    
    asyncio.run(main())

