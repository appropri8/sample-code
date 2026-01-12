"""Simple in-memory vector index for embeddings."""

import numpy as np
from typing import List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
from sklearn.metrics.pairwise import cosine_similarity


@dataclass
class ChunkMetadata:
    """Metadata for a chunk including version and timestamps."""
    doc_id: str
    chunk_id: str
    version: int
    published_at: datetime
    indexed_at: datetime
    source_type: str = "documentation"
    content: str = ""
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "doc_id": self.doc_id,
            "chunk_id": self.chunk_id,
            "version": self.version,
            "published_at": self.published_at.isoformat(),
            "indexed_at": self.indexed_at.isoformat(),
            "source_type": self.source_type
        }


@dataclass
class SearchResult:
    """Result from vector search."""
    doc_id: str
    chunk_id: str
    content: str
    relevance_score: float
    published_at: datetime
    source_type: str
    version: int
    combined_score: Optional[float] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "doc_id": self.doc_id,
            "chunk_id": self.chunk_id,
            "content": self.content[:200] + "..." if len(self.content) > 200 else self.content,
            "relevance_score": self.relevance_score,
            "published_at": self.published_at.isoformat(),
            "source_type": self.source_type,
            "version": self.version,
            "combined_score": self.combined_score
        }


class VectorIndex:
    """Simple in-memory vector index with metadata tracking."""
    
    def __init__(self):
        self.embeddings: List[np.ndarray] = []
        self.chunks: List[str] = []
        self.metadata: List[ChunkMetadata] = []
        self.tombstones: set = set()  # doc_ids that are deleted
    
    def add_chunk(
        self,
        embedding: np.ndarray,
        chunk: str,
        doc_id: str,
        chunk_id: str,
        published_at: datetime,
        version: int = 1,
        source_type: str = "documentation"
    ):
        """Add a chunk with its embedding and metadata."""
        self.embeddings.append(embedding)
        self.chunks.append(chunk)
        self.metadata.append(ChunkMetadata(
            doc_id=doc_id,
            chunk_id=chunk_id,
            version=version,
            published_at=published_at,
            indexed_at=datetime.now(),
            source_type=source_type,
            content=chunk
        ))
    
    def delete_document(self, doc_id: str):
        """Mark document as deleted (tombstone)."""
        self.tombstones.add(doc_id)
    
    def is_deleted(self, doc_id: str) -> bool:
        """Check if document is deleted."""
        return doc_id in self.tombstones
    
    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 10,
        filter_deleted: bool = True
    ) -> List[SearchResult]:
        """Search for similar chunks."""
        if len(self.embeddings) == 0:
            return []
        
        # Convert to numpy array
        embeddings_array = np.array(self.embeddings)
        query_embedding = np.array(query_embedding).reshape(1, -1)
        
        # Normalize for cosine similarity
        query_norm = query_embedding / np.linalg.norm(query_embedding)
        embeddings_norm = embeddings_array / np.linalg.norm(embeddings_array, axis=1, keepdims=True)
        
        # Compute cosine similarity
        similarities = np.dot(embeddings_norm, query_norm.T).flatten()
        
        # Get top-k indices
        top_indices = np.argsort(similarities)[::-1][:top_k * 2]  # Get more to filter
        
        # Build results
        results = []
        for idx in top_indices:
            meta = self.metadata[idx]
            
            # Filter deleted documents
            if filter_deleted and self.is_deleted(meta.doc_id):
                continue
            
            results.append(SearchResult(
                doc_id=meta.doc_id,
                chunk_id=meta.chunk_id,
                content=self.chunks[idx],
                relevance_score=float(similarities[idx]),
                published_at=meta.published_at,
                source_type=meta.source_type,
                version=meta.version
            ))
            
            if len(results) >= top_k:
                break
        
        return results
    
    def get_chunk_count(self) -> int:
        """Get total number of chunks."""
        return len(self.chunks)
    
    def get_doc_ids(self) -> set:
        """Get all document IDs."""
        return {meta.doc_id for meta in self.metadata}
