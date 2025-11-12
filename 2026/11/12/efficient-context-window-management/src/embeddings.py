"""Embedding generation and caching"""

from openai import OpenAI
from typing import List, Dict, Optional
import hashlib
import os


class EmbeddingCache:
    """Cache for embeddings to avoid redundant API calls"""
    
    def __init__(self):
        self.cache = {}
    
    def get_cache_key(self, text: str) -> str:
        """Generate cache key for text."""
        return hashlib.md5(text.encode()).hexdigest()
    
    def get(self, text: str) -> Optional[List[float]]:
        """Get cached embedding."""
        key = self.get_cache_key(text)
        return self.cache.get(key)
    
    def set(self, text: str, embedding: List[float]):
        """Cache embedding."""
        key = self.get_cache_key(text)
        self.cache[key] = embedding
    
    def clear(self):
        """Clear cache."""
        self.cache.clear()


def generate_embeddings(
    chunks: List[Dict],
    model: str = "text-embedding-3-small",
    batch_size: int = 100,
    cache: Optional[EmbeddingCache] = None
) -> List[List[float]]:
    """
    Generate embeddings for text chunks.
    
    Args:
        chunks: List of chunk dictionaries with 'text' field
        model: Embedding model name
        batch_size: Number of chunks to process at once
        cache: Optional embedding cache
    
    Returns:
        List of embedding vectors
    """
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    embeddings = []
    cache = cache or EmbeddingCache()
    
    # Process in batches
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        texts = []
        uncached_indices = []
        
        # Check cache first
        for idx, chunk in enumerate(batch):
            text = chunk["text"]
            cached = cache.get(text)
            if cached:
                embeddings.append(cached)
            else:
                texts.append(text)
                uncached_indices.append(len(embeddings))
                embeddings.append(None)  # Placeholder
        
        # Generate embeddings for uncached texts
        if texts:
            response = client.embeddings.create(
                model=model,
                input=texts
            )
            
            # Fill in embeddings and cache them
            for idx, item in enumerate(response.data):
                embedding = item.embedding
                text = texts[idx]
                cache.set(text, embedding)
                embeddings[uncached_indices[idx]] = embedding
    
    return embeddings

