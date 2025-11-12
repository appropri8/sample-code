"""Tests for vector store"""

import pytest
import numpy as np
from src.vector_store import SimpleVectorStore


def test_add_chunks():
    """Test adding chunks to store"""
    store = SimpleVectorStore()
    chunks = [{"text": "Test chunk 1"}, {"text": "Test chunk 2"}]
    embeddings = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
    
    store.add_chunks(chunks, embeddings)
    assert store.size() == 2


def test_search():
    """Test similarity search"""
    store = SimpleVectorStore()
    chunks = [
        {"text": "Python error handling"},
        {"text": "Context window management"},
        {"text": "RAG applications"}
    ]
    # Simple embeddings (normalized)
    embeddings = [
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0]
    ]
    
    store.add_chunks(chunks, embeddings)
    
    # Search with query similar to first chunk
    query_embedding = [0.9, 0.1, 0.0]
    results = store.search(query_embedding, top_k=2)
    
    assert len(results) <= 2
    assert all(isinstance(result, tuple) and len(result) == 2 for result in results)


def test_search_with_filter():
    """Test search with metadata filter"""
    store = SimpleVectorStore()
    chunks = [
        {"text": "Chunk 1", "metadata": {"type": "A"}},
        {"text": "Chunk 2", "metadata": {"type": "B"}},
        {"text": "Chunk 3", "metadata": {"type": "A"}}
    ]
    embeddings = [[1.0, 0.0], [0.0, 1.0], [0.5, 0.5]]
    
    store.add_chunks(chunks, embeddings)
    
    query_embedding = [1.0, 0.0]
    results = store.search(
        query_embedding,
        top_k=10,
        filter_metadata={"type": "A"}
    )
    
    # Should only return chunks with type "A"
    assert all(chunk["metadata"]["type"] == "A" for chunk, _ in results)


def test_search_min_similarity():
    """Test search with minimum similarity threshold"""
    store = SimpleVectorStore()
    chunks = [{"text": f"Chunk {i}"} for i in range(5)]
    embeddings = [[1.0 if i == j else 0.0 for j in range(5)] for i in range(5)]
    
    store.add_chunks(chunks, embeddings)
    
    query_embedding = [1.0, 0.0, 0.0, 0.0, 0.0]
    results = store.search(query_embedding, top_k=10, min_similarity=0.5)
    
    # Should only return highly similar chunks
    assert all(score >= 0.5 for _, score in results)


def test_clear():
    """Test clearing the store"""
    store = SimpleVectorStore()
    store.add_chunks([{"text": "Test"}], [[0.1, 0.2]])
    assert store.size() == 1
    
    store.clear()
    assert store.size() == 0

