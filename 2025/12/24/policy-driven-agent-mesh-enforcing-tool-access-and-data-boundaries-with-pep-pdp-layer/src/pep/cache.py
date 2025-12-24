"""Decision cache for PEP."""
from typing import Dict, Any, Optional
import time


class DecisionCache:
    """Cache for policy decisions."""
    
    def __init__(self, ttl_seconds: int = 60):
        """Initialize decision cache.
        
        Args:
            ttl_seconds: Time-to-live for cached decisions (default: 60 seconds)
        """
        self.cache = {}
        self.ttl = ttl_seconds
    
    def get(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached decision if not expired.
        
        Args:
            cache_key: Cache key
            
        Returns:
            Cached decision or None if expired/not found
        """
        entry = self.cache.get(cache_key)
        if entry and (time.time() - entry["timestamp"]) < self.ttl:
            return entry["decision"]
        
        # Remove expired entry
        if entry:
            del self.cache[cache_key]
        
        return None
    
    def set(self, cache_key: str, decision: Dict[str, Any]):
        """Cache a decision.
        
        Args:
            cache_key: Cache key
            decision: Decision to cache
        """
        self.cache[cache_key] = {
            "decision": decision,
            "timestamp": time.time()
        }
    
    def clear(self):
        """Clear all cached decisions."""
        self.cache.clear()

