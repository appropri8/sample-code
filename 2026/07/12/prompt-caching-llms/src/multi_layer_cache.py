"""
Multi-layer cache implementation.

Combines multiple caching strategies:
1. L1: In-memory cache (fastest)
2. L2: Redis cache (fast, shared)
3. L3: Semantic cache (flexible)
"""

import hashlib
import time
import redis
from typing import Optional, Tuple
from semantic_cache import SemanticCache


class MultiLayerCache:
    """Multi-layer cache with fallback."""
    
    def __init__(
        self,
        redis_host: str = "localhost",
        redis_port: int = 6379,
        ttl: int = 3600,
        enable_semantic: bool = True,
        semantic_threshold: float = 0.9
    ):
        """
        Initialize multi-layer cache.
        
        Args:
            redis_host: Redis host
            redis_port: Redis port
            ttl: Cache TTL in seconds
            enable_semantic: Whether to enable semantic caching
            semantic_threshold: Similarity threshold for semantic cache
        """
        # L1: In-memory cache (dict)
        self.memory_cache = {}
        self.memory_ttl = {}
        
        # L2: Redis cache
        self.redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        self.ttl = ttl
        
        # L3: Semantic cache (optional)
        self.enable_semantic = enable_semantic
        if enable_semantic:
            self.semantic_cache = SemanticCache(similarity_threshold=semantic_threshold)
        
        # Metrics per layer
        self.l1_hits = 0
        self.l2_hits = 0
        self.l3_hits = 0
        self.misses = 0
    
    def _hash_prompt(self, prompt: str) -> str:
        """Generate cache key from prompt."""
        return hashlib.sha256(prompt.encode()).hexdigest()
    
    def _is_expired(self, key: str) -> bool:
        """Check if memory cache entry is expired."""
        if key not in self.memory_ttl:
            return True
        return time.time() > self.memory_ttl[key]
    
    def get(self, prompt: str) -> Tuple[Optional[str], str]:
        """
        Get cached response, checking all layers.
        
        Args:
            prompt: The prompt to look up
            
        Returns:
            Tuple of (response, source) where source is "L1", "L2", "L3", or None
        """
        cache_key = self._hash_prompt(prompt)
        
        # L1: Memory cache
        if cache_key in self.memory_cache and not self._is_expired(cache_key):
            self.l1_hits += 1
            return (self.memory_cache[cache_key], "L1")
        
        # L2: Redis cache
        cached = self.redis_client.get(cache_key)
        if cached:
            self.l2_hits += 1
            # Promote to L1
            self.memory_cache[cache_key] = cached
            self.memory_ttl[cache_key] = time.time() + 300  # 5 min in memory
            return (cached, "L2")
        
        # L3: Semantic cache (if enabled)
        if self.enable_semantic:
            result = self.semantic_cache.get(prompt)
            if result:
                response, similarity = result
                self.l3_hits += 1
                # Promote to L2 and L1
                self.set(prompt, response)
                return (response, "L3")
        
        # Miss
        self.misses += 1
        return (None, "MISS")
    
    def set(self, prompt: str, response: str):
        """
        Cache a response in all layers.
        
        Args:
            prompt: The prompt
            response: The response to cache
        """
        cache_key = self._hash_prompt(prompt)
        
        # L1: Memory
        self.memory_cache[cache_key] = response
        self.memory_ttl[cache_key] = time.time() + 300  # 5 min
        
        # L2: Redis
        self.redis_client.setex(cache_key, self.ttl, response)
        
        # L3: Semantic
        if self.enable_semantic:
            self.semantic_cache.set(prompt, response)
    
    def stats(self) -> dict:
        """Get cache statistics."""
        total = self.l1_hits + self.l2_hits + self.l3_hits + self.misses
        
        return {
            "l1_hits": self.l1_hits,
            "l2_hits": self.l2_hits,
            "l3_hits": self.l3_hits,
            "misses": self.misses,
            "total_requests": total,
            "l1_hit_ratio": self.l1_hits / total if total > 0 else 0,
            "l2_hit_ratio": self.l2_hits / total if total > 0 else 0,
            "l3_hit_ratio": self.l3_hits / total if total > 0 else 0,
            "overall_hit_ratio": (self.l1_hits + self.l2_hits + self.l3_hits) / total if total > 0 else 0,
        }
    
    def clear(self):
        """Clear all cache layers."""
        self.memory_cache.clear()
        self.memory_ttl.clear()
        self.redis_client.flushdb()
        if self.enable_semantic:
            self.semantic_cache.clear()
        
        self.l1_hits = 0
        self.l2_hits = 0
        self.l3_hits = 0
        self.misses = 0


def mock_llm_call(prompt: str) -> str:
    """Mock LLM call."""
    time.sleep(0.5)
    return f"Response to: {prompt[:50]}..."


def demo_multi_layer_cache():
    """Demonstrate multi-layer caching."""
    print("=== Multi-Layer Cache Demo ===\n")
    
    cache = MultiLayerCache(enable_semantic=True, semantic_threshold=0.85)
    
    # Test queries
    queries = [
        # Exact repeats (should hit L1 after first)
        ("What is Python?", "First request"),
        ("What is Python?", "Exact repeat - L1 hit"),
        
        # Clear L1, should hit L2
        ("What is JavaScript?", "New query"),
        ("What is JavaScript?", "Exact repeat - L1 hit"),
        
        # Semantic similar (should hit L3)
        ("Tell me about Python", "Semantic match"),
        ("Can you explain Python?", "Another semantic match"),
        
        # New query
        ("What is Go?", "New query"),
    ]
    
    for i, (query, description) in enumerate(queries, 1):
        print(f"\nRequest {i}: {query}")
        print(f"Description: {description}")
        
        start = time.time()
        response, source = cache.get(query)
        
        if response:
            latency = time.time() - start
            print(f"  Source: {source}")
            print(f"  Latency: {latency*1000:.1f}ms")
            print(f"  Response: {response}")
        else:
            # Cache miss - call LLM
            response = mock_llm_call(query)
            cache.set(query, response)
            latency = time.time() - start
            print(f"  Source: LLM (cache miss)")
            print(f"  Latency: {latency*1000:.1f}ms")
            print(f"  Response: {response}")
        
        # Clear L1 after query 3 to demonstrate L2
        if i == 3:
            print("\n  [Clearing L1 cache to demonstrate L2...]")
            cache.memory_cache.clear()
            cache.memory_ttl.clear()
    
    # Print statistics
    print("\n" + "="*60)
    print("Cache Statistics")
    print("="*60)
    
    stats = cache.stats()
    print(f"\nTotal Requests: {stats['total_requests']}")
    print(f"\nHits by Layer:")
    print(f"  L1 (Memory):   {stats['l1_hits']} ({stats['l1_hit_ratio']:.1%})")
    print(f"  L2 (Redis):    {stats['l2_hits']} ({stats['l2_hit_ratio']:.1%})")
    print(f"  L3 (Semantic): {stats['l3_hits']} ({stats['l3_hit_ratio']:.1%})")
    print(f"\nCache Misses: {stats['misses']}")
    print(f"Overall Hit Ratio: {stats['overall_hit_ratio']:.1%}")


def compare_single_vs_multi():
    """Compare single-layer vs multi-layer cache."""
    print("\n\n=== Single-Layer vs Multi-Layer Comparison ===\n")
    
    # Single-layer (memory only)
    single_cache = {}
    single_hits = 0
    single_misses = 0
    
    # Multi-layer
    multi_cache = MultiLayerCache(enable_semantic=True, semantic_threshold=0.85)
    
    # Test queries with variations
    queries = [
        "What is Python?",
        "What is Python?",  # Exact repeat
        "Tell me about Python",  # Semantic match
        "What is JavaScript?",
        "Explain JavaScript",  # Semantic match
        "What is Python programming?",  # Semantic match
    ]
    
    print("Testing single-layer cache (exact matching only):")
    for query in queries:
        if query in single_cache:
            single_hits += 1
            print(f"  {query}: HIT")
        else:
            single_misses += 1
            single_cache[query] = f"Response to {query}"
            print(f"  {query}: MISS")
    
    single_ratio = single_hits / len(queries)
    
    print(f"\nSingle-layer hit ratio: {single_ratio:.1%}")
    
    print("\n" + "-"*60 + "\n")
    
    print("Testing multi-layer cache (with semantic matching):")
    for query in queries:
        response, source = multi_cache.get(query)
        if response:
            print(f"  {query}: HIT ({source})")
        else:
            response = f"Response to {query}"
            multi_cache.set(query, response)
            print(f"  {query}: MISS")
    
    multi_stats = multi_cache.stats()
    
    print(f"\nMulti-layer hit ratio: {multi_stats['overall_hit_ratio']:.1%}")
    
    improvement = multi_stats['overall_hit_ratio'] - single_ratio
    print(f"\nImprovement: +{improvement:.1%}")


if __name__ == "__main__":
    demo_multi_layer_cache()
    compare_single_vs_multi()
