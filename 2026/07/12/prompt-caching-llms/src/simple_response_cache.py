"""
Simple response cache using Redis.

Demonstrates basic caching pattern:
1. Hash the prompt
2. Check Redis cache
3. If hit, return cached response
4. If miss, call LLM and cache the response
"""

import hashlib
import time
import redis
from typing import Optional


class SimpleResponseCache:
    """Basic response cache with Redis."""
    
    def __init__(self, host: str = "localhost", port: int = 6379, ttl: int = 3600):
        """
        Initialize cache.
        
        Args:
            host: Redis host
            port: Redis port
            ttl: Time-to-live for cache entries in seconds
        """
        self.redis_client = redis.Redis(host=host, port=port, decode_responses=True)
        self.ttl = ttl
        self.hits = 0
        self.misses = 0
    
    def _hash_prompt(self, prompt: str) -> str:
        """Generate cache key from prompt."""
        return hashlib.sha256(prompt.encode()).hexdigest()
    
    def get(self, prompt: str) -> Optional[str]:
        """
        Get cached response for prompt.
        
        Args:
            prompt: The prompt to look up
            
        Returns:
            Cached response if found, None otherwise
        """
        cache_key = self._hash_prompt(prompt)
        cached = self.redis_client.get(cache_key)
        
        if cached:
            self.hits += 1
            return cached
        
        self.misses += 1
        return None
    
    def set(self, prompt: str, response: str):
        """
        Cache a response.
        
        Args:
            prompt: The prompt
            response: The response to cache
        """
        cache_key = self._hash_prompt(prompt)
        self.redis_client.setex(cache_key, self.ttl, response)
    
    def hit_ratio(self) -> float:
        """Calculate cache hit ratio."""
        total = self.hits + self.misses
        if total == 0:
            return 0.0
        return self.hits / total
    
    def stats(self) -> dict:
        """Get cache statistics."""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "hit_ratio": self.hit_ratio(),
            "total_requests": self.hits + self.misses
        }
    
    def clear(self):
        """Clear all cache entries (use with caution)."""
        self.redis_client.flushdb()
        self.hits = 0
        self.misses = 0


def mock_llm_call(prompt: str) -> str:
    """
    Mock LLM call that takes time.
    In production, replace with actual LLM API call.
    """
    time.sleep(0.5)  # Simulate API latency
    return f"Response to: {prompt[:50]}..."


def demo_simple_cache():
    """Demonstrate simple caching."""
    print("=== Simple Response Cache Demo ===\n")
    
    cache = SimpleResponseCache(ttl=3600)
    
    # Sample prompts
    prompts = [
        "What is Python?",
        "What is JavaScript?",
        "What is Python?",  # Duplicate - should hit cache
        "What is Go?",
        "What is JavaScript?",  # Duplicate - should hit cache
        "What is Python?",  # Duplicate - should hit cache
    ]
    
    for i, prompt in enumerate(prompts, 1):
        print(f"\nRequest {i}: {prompt}")
        
        # Check cache
        start = time.time()
        cached = cache.get(prompt)
        
        if cached:
            response = cached
            source = "CACHE"
        else:
            response = mock_llm_call(prompt)
            cache.set(prompt, response)
            source = "LLM"
        
        elapsed = time.time() - start
        print(f"  Source: {source}")
        print(f"  Latency: {elapsed*1000:.0f}ms")
        print(f"  Response: {response}")
    
    # Print statistics
    print("\n=== Cache Statistics ===")
    stats = cache.stats()
    print(f"Total Requests: {stats['total_requests']}")
    print(f"Cache Hits: {stats['hits']}")
    print(f"Cache Misses: {stats['misses']}")
    print(f"Hit Ratio: {stats['hit_ratio']:.1%}")
    
    # Calculate cost savings (assuming $0.01 per 1K tokens, 100 tokens per request)
    tokens_per_request = 100
    cost_per_1k = 0.01
    
    cost_without_cache = stats['total_requests'] * (tokens_per_request / 1000) * cost_per_1k
    
    # Cache hits cost 10% of normal (provider-dependent)
    cost_with_cache = (
        stats['hits'] * (tokens_per_request / 1000) * cost_per_1k * 0.1 +
        stats['misses'] * (tokens_per_request / 1000) * cost_per_1k
    )
    
    savings = cost_without_cache - cost_with_cache
    savings_percent = (savings / cost_without_cache) * 100 if cost_without_cache > 0 else 0
    
    print(f"\n=== Cost Analysis ===")
    print(f"Cost without cache: ${cost_without_cache:.4f}")
    print(f"Cost with cache: ${cost_with_cache:.4f}")
    print(f"Savings: ${savings:.4f} ({savings_percent:.1f}%)")


if __name__ == "__main__":
    demo_simple_cache()
