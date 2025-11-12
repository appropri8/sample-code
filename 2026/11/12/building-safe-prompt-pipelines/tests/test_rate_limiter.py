"""Tests for rate limiting"""

import pytest
import time
from src.rate_limiter import RateLimiter, RateLimitError

def test_rate_limiter_initialization():
    """Test rate limiter initialization"""
    limiter = RateLimiter(max_requests=10, window_seconds=60)
    
    assert limiter.max_requests == 10
    assert limiter.window_seconds == 60

def test_rate_limiter_allows_requests():
    """Test that rate limiter allows requests within limit"""
    limiter = RateLimiter(max_requests=5, window_seconds=60)
    
    for i in range(5):
        assert limiter.check_limit("user1") is True

def test_rate_limiter_blocks_excess_requests():
    """Test that rate limiter blocks excess requests"""
    limiter = RateLimiter(max_requests=3, window_seconds=60)
    
    # Use up the limit
    for i in range(3):
        assert limiter.check_limit("user1") is True
    
    # Next request should be blocked
    assert limiter.check_limit("user1") is False

def test_rate_limiter_resets():
    """Test that rate limiter can be reset"""
    limiter = RateLimiter(max_requests=3, window_seconds=60)
    
    # Use up the limit
    for i in range(3):
        limiter.check_limit("user1")
    
    # Reset
    limiter.reset("user1")
    
    # Should be able to make requests again
    assert limiter.check_limit("user1") is True

def test_rate_limiter_per_user():
    """Test that rate limiting is per user"""
    limiter = RateLimiter(max_requests=2, window_seconds=60)
    
    # User1 uses limit
    limiter.check_limit("user1")
    limiter.check_limit("user1")
    
    # User2 should still have requests
    assert limiter.check_limit("user2") is True
    assert limiter.check_limit("user2") is True

