"""Rate limiting for prompt pipelines"""

import time
from collections import defaultdict
from typing import Dict

class RateLimitError(Exception):
    """Raised when rate limit is exceeded"""
    pass

class RateLimiter:
    """Simple rate limiter"""
    
    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        """
        Initialize rate limiter
        
        Args:
            max_requests: Maximum requests per window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)
    
    def check_limit(self, user_id: str) -> bool:
        """
        Check if user has exceeded rate limit
        
        Args:
            user_id: User identifier
            
        Returns:
            True if within limit, False if exceeded
        """
        now = time.time()
        user_requests = self.requests[user_id]
        
        # Remove old requests
        user_requests[:] = [
            req_time for req_time in user_requests 
            if now - req_time < self.window_seconds
        ]
        
        if len(user_requests) >= self.max_requests:
            return False
        
        user_requests.append(now)
        return True
    
    def reset(self, user_id: str):
        """Reset rate limit for a user"""
        if user_id in self.requests:
            del self.requests[user_id]

