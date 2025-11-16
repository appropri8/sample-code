"""Tests for retry and timeout utilities."""

import pytest
import asyncio
from src.retry_timeout import retry_with_backoff, should_retry


class TestRetryLogic:
    """Test retry logic."""
    
    @pytest.mark.asyncio
    async def test_success_on_first_try(self):
        """Test that successful call doesn't retry."""
        call_count = 0
        
        async def success_func():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = await retry_with_backoff(success_func, max_attempts=3)
        assert result == "success"
        assert call_count == 1
    
    @pytest.mark.asyncio
    async def test_retry_on_failure(self):
        """Test that failed call retries."""
        call_count = 0
        
        async def fail_then_succeed():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Fail")
            return "success"
        
        result = await retry_with_backoff(fail_then_succeed, max_attempts=5)
        assert result == "success"
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self):
        """Test that max retries are respected."""
        call_count = 0
        
        async def always_fail():
            nonlocal call_count
            call_count += 1
            raise Exception("Always fail")
        
        with pytest.raises(Exception, match="Always fail"):
            await retry_with_backoff(always_fail, max_attempts=3)
        
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_timeout(self):
        """Test timeout handling."""
        async def slow_func():
            await asyncio.sleep(2.0)
            return "success"
        
        with pytest.raises(asyncio.TimeoutError):
            await retry_with_backoff(slow_func, max_attempts=2, timeout=0.5)
    
    def test_should_retry(self):
        """Test retry decision logic."""
        # Should retry server errors
        class ServerError(Exception):
            status_code = 500
        
        assert should_retry(ServerError()) is True
        
        # Should not retry client errors
        class ClientError(Exception):
            status_code = 400
        
        assert should_retry(ClientError()) is False
        
        # Should not retry validation errors
        assert should_retry(ValueError("Invalid")) is False
        assert should_retry(KeyError("Missing")) is False

