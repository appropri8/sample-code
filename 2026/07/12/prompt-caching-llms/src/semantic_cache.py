"""
Semantic cache using embeddings.

Matches prompts by meaning, not exact text.
Uses sentence transformers to compute embeddings and cosine similarity.
"""

import numpy as np
from typing import Optional, List, Tuple
from sentence_transformers import SentenceTransformer


class SemanticCache:
    """Cache that matches prompts by semantic similarity."""
    
    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        similarity_threshold: float = 0.9,
        max_cache_size: int = 1000
    ):
        """
        Initialize semantic cache.
        
        Args:
            model_name: Sentence transformer model name
            similarity_threshold: Minimum similarity score for cache hit (0-1)
            max_cache_size: Maximum number of entries to cache
        """
        self.model = SentenceTransformer(model_name)
        self.similarity_threshold = similarity_threshold
        self.max_cache_size = max_cache_size
        
        # Storage
        self.prompts: List[str] = []
        self.embeddings: List[np.ndarray] = []
        self.responses: List[str] = []
        
        # Metrics
        self.hits = 0
        self.misses = 0
    
    def _compute_embedding(self, text: str) -> np.ndarray:
        """Compute embedding for text."""
        return self.model.encode(text, convert_to_numpy=True)
    
    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Compute cosine similarity between two vectors."""
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
    
    def get(self, prompt: str) -> Optional[Tuple[str, float]]:
        """
        Get cached response for prompt.
        
        Args:
            prompt: The prompt to look up
            
        Returns:
            Tuple of (response, similarity_score) if found, None otherwise
        """
        if not self.prompts:
            self.misses += 1
            return None
        
        # Compute embedding for query
        query_embedding = self._compute_embedding(prompt)
        
        # Find best match
        best_similarity = 0.0
        best_idx = -1
        
        for i, cached_embedding in enumerate(self.embeddings):
            similarity = self._cosine_similarity(query_embedding, cached_embedding)
            if similarity > best_similarity:
                best_similarity = similarity
                best_idx = i
        
        # Check if best match is above threshold
        if best_similarity >= self.similarity_threshold:
            self.hits += 1
            return (self.responses[best_idx], best_similarity)
        
        self.misses += 1
        return None
    
    def set(self, prompt: str, response: str):
        """
        Cache a response.
        
        Args:
            prompt: The prompt
            response: The response to cache
        """
        # Compute embedding
        embedding = self._compute_embedding(prompt)
        
        # Add to cache
        self.prompts.append(prompt)
        self.embeddings.append(embedding)
        self.responses.append(response)
        
        # Evict oldest if over limit
        if len(self.prompts) > self.max_cache_size:
            self.prompts.pop(0)
            self.embeddings.pop(0)
            self.responses.pop(0)
    
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
            "cache_size": len(self.prompts),
            "total_requests": self.hits + self.misses
        }
    
    def clear(self):
        """Clear cache."""
        self.prompts.clear()
        self.embeddings.clear()
        self.responses.clear()
        self.hits = 0
        self.misses = 0


def demo_semantic_cache():
    """Demonstrate semantic caching."""
    print("=== Semantic Cache Demo ===\n")
    
    cache = SemanticCache(similarity_threshold=0.85)
    
    # Cache some responses
    print("Caching responses...\n")
    
    cache.set("What is Python?", "Python is a high-level programming language.")
    cache.set("How do I reset my password?", "Click 'Forgot Password' on the login page.")
    cache.set("What are your refund terms?", "Refunds are available within 60 days.")
    
    # Try semantically similar queries
    queries = [
        ("What is Python?", "Exact match"),
        ("Tell me about Python", "Similar phrasing"),
        ("Can you explain Python?", "Similar meaning"),
        ("What's Python programming language?", "Related but different"),
        ("How to reset password?", "Similar to cached query"),
        ("Password reset instructions", "Related concept"),
        ("What is JavaScript?", "Different topic - should miss"),
    ]
    
    print("Testing semantic matching:\n")
    
    for query, description in queries:
        result = cache.get(query)
        
        if result:
            response, similarity = result
            print(f"Query: {query}")
            print(f"  Description: {description}")
            print(f"  Status: HIT (similarity: {similarity:.3f})")
            print(f"  Response: {response}")
        else:
            print(f"Query: {query}")
            print(f"  Description: {description}")
            print(f"  Status: MISS")
        print()
    
    # Print statistics
    print("=== Cache Statistics ===")
    stats = cache.stats()
    print(f"Total Requests: {stats['total_requests']}")
    print(f"Cache Hits: {stats['hits']}")
    print(f"Cache Misses: {stats['misses']}")
    print(f"Hit Ratio: {stats['hit_ratio']:.1%}")
    print(f"Cache Size: {stats['cache_size']}")


def compare_exact_vs_semantic():
    """Compare exact matching vs semantic matching."""
    print("\n\n=== Exact vs Semantic Comparison ===\n")
    
    # Exact cache (using dict)
    exact_cache = {}
    exact_hits = 0
    exact_misses = 0
    
    # Semantic cache
    semantic_cache = SemanticCache(similarity_threshold=0.85)
    
    # Pre-populate caches
    base_prompts = [
        "What is Python?",
        "How do I reset my password?",
        "What are your shipping rates?",
    ]
    
    for prompt in base_prompts:
        response = f"Response to: {prompt}"
        exact_cache[prompt] = response
        semantic_cache.set(prompt, response)
    
    # Test queries (variations of base prompts)
    test_queries = [
        "What is Python?",  # Exact match
        "Tell me about Python",  # Semantic match
        "Can you explain Python?",  # Semantic match
        "How do I reset my password?",  # Exact match
        "How to reset password?",  # Semantic match
        "Password reset help",  # Semantic match
        "What are your shipping rates?",  # Exact match
        "How much does shipping cost?",  # Semantic match
    ]
    
    print("Testing queries:\n")
    
    for query in test_queries:
        # Exact cache
        if query in exact_cache:
            exact_hits += 1
            exact_status = "HIT"
        else:
            exact_misses += 1
            exact_status = "MISS"
        
        # Semantic cache
        semantic_result = semantic_cache.get(query)
        if semantic_result:
            semantic_status = f"HIT ({semantic_result[1]:.3f})"
        else:
            semantic_status = "MISS"
        
        print(f"Query: {query}")
        print(f"  Exact cache: {exact_status}")
        print(f"  Semantic cache: {semantic_status}")
        print()
    
    # Compare results
    exact_total = exact_hits + exact_misses
    exact_ratio = exact_hits / exact_total if exact_total > 0 else 0
    
    semantic_stats = semantic_cache.stats()
    
    print("=== Comparison ===")
    print(f"\nExact Cache:")
    print(f"  Hits: {exact_hits}")
    print(f"  Misses: {exact_misses}")
    print(f"  Hit Ratio: {exact_ratio:.1%}")
    
    print(f"\nSemantic Cache:")
    print(f"  Hits: {semantic_stats['hits']}")
    print(f"  Misses: {semantic_stats['misses']}")
    print(f"  Hit Ratio: {semantic_stats['hit_ratio']:.1%}")
    
    improvement = semantic_stats['hit_ratio'] - exact_ratio
    print(f"\nImprovement: {improvement:.1%}")


if __name__ == "__main__":
    demo_semantic_cache()
    compare_exact_vs_semantic()
