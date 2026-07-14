"""
OpenAI caching patterns.

OpenAI doesn't have explicit prompt caching API (as of early 2024),
but this demonstrates application-level caching patterns for OpenAI.
"""

import os
import hashlib
import json
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Check if openai is available
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("Warning: openai package not installed. Install with: pip install openai")


class OpenAICacheWrapper:
    """
    Wrapper for OpenAI API with application-level caching.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize with API key.
        
        Args:
            api_key: OpenAI API key (or from OPENAI_API_KEY env var)
        """
        if not OPENAI_AVAILABLE:
            raise ImportError("openai package required")
        
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found")
        
        self.client = OpenAI(api_key=self.api_key)
        self.cache = {}  # Simple in-memory cache
        
        self.hits = 0
        self.misses = 0
    
    def _compute_cache_key(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        Compute cache key from messages and parameters.
        
        Args:
            messages: Chat messages
            **kwargs: Additional parameters (model, temperature, etc.)
            
        Returns:
            Cache key (hash)
        """
        # Create deterministic representation
        cache_input = {
            "messages": messages,
            "model": kwargs.get("model", "gpt-3.5-turbo"),
            "temperature": kwargs.get("temperature", 1.0),
            "max_tokens": kwargs.get("max_tokens"),
        }
        
        # Sort keys for consistency
        cache_str = json.dumps(cache_input, sort_keys=True)
        
        # Hash
        return hashlib.sha256(cache_str.encode()).hexdigest()
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        use_cache: bool = True,
        **kwargs
    ) -> Any:
        """
        Create chat completion with optional caching.
        
        Args:
            messages: Chat messages
            use_cache: Whether to use cache
            **kwargs: Additional parameters for OpenAI API
            
        Returns:
            OpenAI response
        """
        # Check cache
        if use_cache:
            cache_key = self._compute_cache_key(messages, **kwargs)
            
            if cache_key in self.cache:
                self.hits += 1
                print(f"[Cache HIT]")
                return self.cache[cache_key]
        
        # Cache miss - call API
        self.misses += 1
        print(f"[Cache MISS]")
        
        response = self.client.chat.completions.create(
            messages=messages,
            **kwargs
        )
        
        # Cache the response
        if use_cache:
            self.cache[cache_key] = response
        
        return response
    
    def stats(self) -> dict:
        """Get cache statistics."""
        total = self.hits + self.misses
        return {
            "hits": self.hits,
            "misses": self.misses,
            "total": total,
            "hit_ratio": self.hits / total if total > 0 else 0,
            "cache_size": len(self.cache)
        }


def demo_basic_caching():
    """Demonstrate basic caching with OpenAI."""
    print("=== Basic OpenAI Caching Demo ===\n")
    
    if not OPENAI_AVAILABLE:
        print("OpenAI package not installed.")
        return
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("OPENAI_API_KEY not found in environment.")
        return
    
    try:
        client = OpenAICacheWrapper(api_key)
        
        system_prompt = "You are a helpful assistant. Be concise."
        
        # First request
        print("Request 1: What is Python?")
        response_1 = client.chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "What is Python?"}
            ],
            model="gpt-3.5-turbo",
            max_tokens=100
        )
        print(f"Response: {response_1.choices[0].message.content[:100]}...")
        print()
        
        # Second request - exact same (should hit cache)
        print("Request 2: What is Python? (exact repeat)")
        response_2 = client.chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "What is Python?"}
            ],
            model="gpt-3.5-turbo",
            max_tokens=100
        )
        print(f"Response: {response_2.choices[0].message.content[:100]}...")
        print()
        
        # Third request - different query (should miss)
        print("Request 3: What is JavaScript? (new query)")
        response_3 = client.chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "What is JavaScript?"}
            ],
            model="gpt-3.5-turbo",
            max_tokens=100
        )
        print(f"Response: {response_3.choices[0].message.content[:100]}...")
        print()
        
        # Print stats
        stats = client.stats()
        print("\n=== Cache Statistics ===")
        print(f"Total Requests: {stats['total']}")
        print(f"Cache Hits: {stats['hits']}")
        print(f"Cache Misses: {stats['misses']}")
        print(f"Hit Ratio: {stats['hit_ratio']:.1%}")
        
    except Exception as e:
        print(f"Error: {e}")


def demo_stable_system_prompts():
    """
    Demonstrate how stable system prompts improve caching.
    """
    print("\n\n=== Stable System Prompts Demo ===\n")
    
    if not OPENAI_AVAILABLE or not os.getenv("OPENAI_API_KEY"):
        print("OpenAI not available or API key not set.")
        return
    
    client = OpenAICacheWrapper()
    
    # Good pattern: Stable system prompt
    STABLE_SYSTEM_PROMPT = """You are a customer support assistant.
Be helpful and professional.
Check documentation before answering."""
    
    print("Using stable system prompt across requests:\n")
    
    queries = [
        "How do I reset my password?",
        "What are your shipping rates?",
        "How do I reset my password?",  # Repeat - should cache
        "What are your shipping rates?",  # Repeat - should cache
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"Request {i}: {query}")
        response = client.chat_completion(
            messages=[
                {"role": "system", "content": STABLE_SYSTEM_PROMPT},
                {"role": "user", "content": query}
            ],
            model="gpt-3.5-turbo",
            max_tokens=100
        )
        print()
    
    stats = client.stats()
    print("=== Results ===")
    print(f"Hit Ratio: {stats['hit_ratio']:.1%}")
    print(f"Cache saved {stats['hits']} API calls")


def demo_cache_key_sensitivity():
    """
    Show how small changes affect caching.
    """
    print("\n\n=== Cache Key Sensitivity Demo ===\n")
    
    if not OPENAI_AVAILABLE or not os.getenv("OPENAI_API_KEY"):
        print("OpenAI not available or API key not set.")
        return
    
    client = OpenAICacheWrapper()
    
    base_messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is Python?"}
    ]
    
    # Test 1: Exact same messages
    print("Test 1: Exact same messages")
    client.chat_completion(messages=base_messages, model="gpt-3.5-turbo", max_tokens=50)
    client.chat_completion(messages=base_messages, model="gpt-3.5-turbo", max_tokens=50)
    print()
    
    # Test 2: Different whitespace (same after normalization)
    print("Test 2: Extra whitespace")
    messages_whitespace = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is Python? "}  # Extra space
    ]
    client.chat_completion(messages=messages_whitespace, model="gpt-3.5-turbo", max_tokens=50)
    print()
    
    # Test 3: Different temperature (different cache key)
    print("Test 3: Different temperature")
    client.chat_completion(messages=base_messages, model="gpt-3.5-turbo", max_tokens=50, temperature=0.5)
    print()
    
    # Test 4: Different model (different cache key)
    print("Test 4: Different model")
    client.chat_completion(messages=base_messages, model="gpt-4", max_tokens=50)
    print()
    
    stats = client.stats()
    print("=== Cache Behavior ===")
    print(f"Total requests: {stats['total']}")
    print(f"Cache hits: {stats['hits']}")
    print(f"Cache misses: {stats['misses']}")
    print("\nNote: Whitespace differences cause cache misses.")
    print("Use normalization to improve hit rate.")


if __name__ == "__main__":
    demo_basic_caching()
    # Uncomment to run more examples:
    # demo_stable_system_prompts()
    # demo_cache_key_sensitivity()
