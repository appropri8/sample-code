"""Simple vector store for embeddings"""

import numpy as np
from typing import List, Tuple, Dict, Optional


class SimpleVectorStore:
    """Simple in-memory vector store for embeddings"""
    
    def __init__(self):
        self.embeddings = []
        self.chunks = []
        self.metadata = []
    
    def add_chunks(
        self,
        chunks: List[Dict],
        embeddings: List[List[float]]
    ):
        """Add chunks and embeddings to the store."""
        if len(chunks) != len(embeddings):
            raise ValueError("Chunks and embeddings must have same length")
        
        self.chunks.extend(chunks)
        self.embeddings.extend(embeddings)
        self.metadata.extend([chunk.get("metadata", {}) for chunk in chunks])
    
    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filter_metadata: Optional[Dict] = None,
        min_similarity: float = 0.0
    ) -> List[Tuple[Dict, float]]:
        """
        Search for similar chunks.
        
        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return
            filter_metadata: Optional metadata filters
            min_similarity: Minimum similarity threshold
        
        Returns:
            List of (chunk, similarity_score) tuples
        """
        if not self.embeddings:
            return []
        
        # Convert to numpy array for efficient computation
        embeddings_array = np.array(self.embeddings)
        query_array = np.array(query_embedding)
        
        # Compute cosine similarity
        norms = np.linalg.norm(embeddings_array, axis=1)
        query_norm = np.linalg.norm(query_array)
        
        # Avoid division by zero
        norms = np.where(norms == 0, 1, norms)
        query_norm = query_norm if query_norm > 0 else 1
        
        similarities = np.dot(embeddings_array, query_array) / (norms * query_norm)
        
        # Apply metadata filters if provided
        indices = list(range(len(self.chunks)))
        if filter_metadata:
            indices = [
                i for i in indices
                if all(
                    self.metadata[i].get(k) == v
                    for k, v in filter_metadata.items()
                )
            ]
        
        # Filter by similarity threshold
        if min_similarity > 0:
            indices = [i for i in indices if similarities[i] >= min_similarity]
        
        # Get top-k results
        if not indices:
            return []
        
        indexed_similarities = [(i, similarities[i]) for i in indices]
        indexed_similarities.sort(key=lambda x: x[1], reverse=True)
        top_indices = [i for i, _ in indexed_similarities[:top_k]]
        
        results = [
            (self.chunks[i], float(similarities[i]))
            for i in top_indices
        ]
        
        return results
    
    def clear(self):
        """Clear all stored data."""
        self.embeddings = []
        self.chunks = []
        self.metadata = []
    
    def size(self) -> int:
        """Get number of stored chunks."""
        return len(self.chunks)

