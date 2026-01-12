"""Content hashing and version tracking for incremental indexing."""

import hashlib
from datetime import datetime
from typing import Optional, Dict
from dataclasses import dataclass, field


@dataclass
class DocumentMetadata:
    """Metadata for a document including version and timestamps."""
    doc_id: str
    content: str
    content_hash: str
    published_at: datetime
    indexed_at: datetime
    version: int = 1
    source_type: str = "documentation"  # policy, product, documentation, historical
    
    def __post_init__(self):
        """Compute hash if not provided."""
        if not self.content_hash:
            self.content_hash = self._compute_hash(self.content)
    
    @staticmethod
    def _compute_hash(content: str) -> str:
        """Compute SHA256 hash of content."""
        return hashlib.sha256(content.encode()).hexdigest()
    
    def update(self, new_content: str, new_published_at: datetime):
        """Update document and increment version."""
        self.content = new_content
        self.content_hash = self._compute_hash(new_content)
        self.published_at = new_published_at
        self.indexed_at = datetime.now()
        self.version += 1
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "doc_id": self.doc_id,
            "content_hash": self.content_hash,
            "published_at": self.published_at.isoformat(),
            "indexed_at": self.indexed_at.isoformat(),
            "version": self.version,
            "source_type": self.source_type
        }


class DocumentTracker:
    """Tracks document changes using content hashing."""
    
    def __init__(self):
        self.doc_hashes: Dict[str, str] = {}  # doc_id -> content_hash
        self.last_indexed: Dict[str, datetime] = {}  # doc_id -> timestamp
        self.metadata: Dict[str, DocumentMetadata] = {}  # doc_id -> metadata
        self.tombstones: set = set()  # doc_ids that are deleted
    
    def compute_hash(self, content: str) -> str:
        """Compute content hash to detect changes."""
        return hashlib.sha256(content.encode()).hexdigest()
    
    def has_changed(self, doc_id: str, content: str) -> bool:
        """Check if document content has changed."""
        current_hash = self.compute_hash(content)
        old_hash = self.doc_hashes.get(doc_id)
        
        if old_hash is None:
            return True  # New document
        
        return current_hash != old_hash
    
    def mark_indexed(
        self,
        doc_id: str,
        content: str,
        published_at: datetime,
        source_type: str = "documentation"
    ):
        """Mark document as indexed with current hash."""
        current_hash = self.compute_hash(content)
        self.doc_hashes[doc_id] = current_hash
        self.last_indexed[doc_id] = datetime.now()
        
        # Update or create metadata
        if doc_id in self.metadata:
            self.metadata[doc_id].update(content, published_at)
        else:
            self.metadata[doc_id] = DocumentMetadata(
                doc_id=doc_id,
                content=content,
                content_hash=current_hash,
                published_at=published_at,
                indexed_at=datetime.now(),
                version=1,
                source_type=source_type
            )
    
    def get_metadata(self, doc_id: str) -> Optional[DocumentMetadata]:
        """Get metadata for a document."""
        return self.metadata.get(doc_id)
    
    def delete_document(self, doc_id: str):
        """Mark document as deleted (tombstone)."""
        self.tombstones.add(doc_id)
        # Optionally remove from tracking
        if doc_id in self.doc_hashes:
            del self.doc_hashes[doc_id]
        if doc_id in self.last_indexed:
            del self.last_indexed[doc_id]
    
    def is_deleted(self, doc_id: str) -> bool:
        """Check if document is deleted."""
        return doc_id in self.tombstones
    
    def get_version(self, doc_id: str) -> int:
        """Get current version of document."""
        if doc_id in self.metadata:
            return self.metadata[doc_id].version
        return 0
