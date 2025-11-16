"""Tests for fallback chain."""

import pytest
import asyncio
from src.fallback_chain import (
    PrimaryTool,
    CachedTool,
    ReadOnlyTool,
    ToolWithFallback,
    ToolError
)


class TestFallbackChain:
    """Test fallback chain logic."""
    
    @pytest.mark.asyncio
    async def test_primary_succeeds(self):
        """Test that primary tool is used when it succeeds."""
        primary = PrimaryTool("test", simulate_failure=False)
        cached = CachedTool("test")
        readonly = ReadOnlyTool("test")
        
        tool = ToolWithFallback(primary, [cached, readonly])
        result = await tool.call({"param": "value"})
        
        assert result["source"] == "primary"
        assert tool.fallback_used is False
    
    @pytest.mark.asyncio
    async def test_fallback_to_cache(self):
        """Test fallback to cache when primary fails."""
        primary = PrimaryTool("test", simulate_failure=True)
        cached = CachedTool("test", cache={"()": "cached result"})
        readonly = ReadOnlyTool("test")
        
        tool = ToolWithFallback(primary, [cached, readonly])
        result = await tool.call({})
        
        assert result["source"] == "cache"
        assert tool.fallback_used is True
    
    @pytest.mark.asyncio
    async def test_fallback_to_readonly(self):
        """Test fallback to read-only when primary and cache fail."""
        primary = PrimaryTool("test", simulate_failure=True)
        cached = CachedTool("test", cache={})
        readonly = ReadOnlyTool("test")
        
        tool = ToolWithFallback(primary, [cached, readonly])
        result = await tool.call({"param": "value"})
        
        assert result["source"] == "readonly"
        assert tool.fallback_used is True
    
    @pytest.mark.asyncio
    async def test_all_fail(self):
        """Test that exception is raised when all tools fail."""
        primary = PrimaryTool("test", simulate_failure=True)
        cached = CachedTool("test", cache={})
        
        class FailingReadOnly(ReadOnlyTool):
            async def call(self, params):
                raise ToolError("Read-only failed")
        
        failing_readonly = FailingReadOnly("test")
        tool = ToolWithFallback(primary, [cached, failing_readonly])
        
        with pytest.raises(ToolError):
            await tool.call({})

