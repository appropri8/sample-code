"""Incremental ingestion: only re-embed changed chunks."""

import os
import argparse
import pickle
from pathlib import Path
from datetime import datetime
from typing import List, Tuple
import numpy as np

from src.document_tracker import DocumentTracker
from src.vector_index import VectorIndex


def chunk_document(content: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """Split document into chunks with overlap.
    
    Args:
        content: Document content
        chunk_size: Target chunk size in characters
        overlap: Overlap between chunks in characters
    
    Returns:
        List of chunks
    """
    if len(content) <= chunk_size:
        return [content]
    
    chunks = []
    start = 0
    
    while start < len(content):
        end = start + chunk_size
        chunk = content[start:end]
        chunks.append(chunk)
        start = end - overlap
    
    return chunks


def generate_embeddings(texts: List[str]) -> List[np.ndarray]:
    """Generate embeddings for texts.
    
    In a real implementation, this would call OpenAI or another embedding API.
    For this example, we use random embeddings.
    
    Args:
        texts: List of text chunks
    
    Returns:
        List of embedding vectors
    """
    # In production, use OpenAI or another embedding service
    # For demo purposes, use random embeddings
    embeddings = []
    for text in texts:
        # Simulate 1536-dimensional embedding (OpenAI ada-002)
        embedding = np.random.rand(1536).astype(np.float32)
        # Normalize
        embedding = embedding / np.linalg.norm(embedding)
        embeddings.append(embedding)
    
    return embeddings


def get_file_mtime(file_path: Path) -> datetime:
    """Get file modification time as published_at."""
    mtime = os.path.getmtime(file_path)
    return datetime.fromtimestamp(mtime)


def infer_source_type(file_path: Path) -> str:
    """Infer source type from file path."""
    path_str = str(file_path).lower()
    if "policy" in path_str:
        return "policy"
    elif "product" in path_str or "catalog" in path_str:
        return "product"
    elif "api" in path_str or "docs" in path_str:
        return "documentation"
    else:
        return "documentation"


def crawl_documents(source_dir: Path) -> List[Tuple[Path, str, datetime, str]]:
    """Crawl documents from directory.
    
    Args:
        source_dir: Directory to crawl
    
    Returns:
        List of (file_path, content, published_at, source_type) tuples
    """
    documents = []
    
    for file_path in source_dir.rglob("*.md"):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            published_at = get_file_mtime(file_path)
            source_type = infer_source_type(file_path)
            doc_id = file_path.stem
            
            documents.append((file_path, content, published_at, source_type))
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
    
    return documents


def incremental_ingest(
    source_dir: Path,
    tracker: DocumentTracker,
    index: VectorIndex,
    force_reindex: bool = False
):
    """Incrementally ingest documents, only re-embedding changed ones.
    
    Args:
        source_dir: Directory containing documents
        tracker: Document tracker for change detection
        index: Vector index to update
        force_reindex: If True, re-index all documents
    """
    documents = crawl_documents(source_dir)
    
    print(f"Found {len(documents)} documents")
    
    for file_path, content, published_at, source_type in documents:
        doc_id = file_path.stem
        
        # Check if document has changed
        if not force_reindex and not tracker.has_changed(doc_id, content):
            print(f"  Skipping {doc_id} (unchanged)")
            continue
        
        print(f"  Processing {doc_id}...")
        
        # Chunk document
        chunks = chunk_document(content)
        print(f"    Split into {len(chunks)} chunks")
        
        # Generate embeddings
        embeddings = generate_embeddings(chunks)
        print(f"    Generated {len(embeddings)} embeddings")
        
        # Get current version
        current_version = tracker.get_version(doc_id)
        new_version = current_version + 1 if current_version > 0 else 1
        
        # Add chunks to index
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            chunk_id = f"{doc_id}_chunk_{i}"
            index.add_chunk(
                embedding=embedding,
                chunk=chunk,
                doc_id=doc_id,
                chunk_id=chunk_id,
                published_at=published_at,
                version=new_version,
                source_type=source_type
            )
        
        # Mark as indexed
        tracker.mark_indexed(doc_id, content, published_at, source_type)
        print(f"    Indexed as version {new_version}")


def main():
    parser = argparse.ArgumentParser(description="Incremental document ingestion")
    parser.add_argument(
        "--source-dir",
        type=str,
        required=True,
        help="Directory containing documents to index"
    )
    parser.add_argument(
        "--index-file",
        type=str,
        default="index.pkl",
        help="File to save/load index"
    )
    parser.add_argument(
        "--tracker-file",
        type=str,
        default="tracker.pkl",
        help="File to save/load tracker"
    )
    parser.add_argument(
        "--force-reindex",
        action="store_true",
        help="Force re-indexing of all documents"
    )
    
    args = parser.parse_args()
    
    source_dir = Path(args.source_dir)
    if not source_dir.exists():
        print(f"Error: {source_dir} does not exist")
        return
    
    # Load or create tracker
    tracker = DocumentTracker()
    if os.path.exists(args.tracker_file) and not args.force_reindex:
        with open(args.tracker_file, "rb") as f:
            tracker = pickle.load(f)
        print(f"Loaded tracker from {args.tracker_file}")
    
    # Load or create index
    index = VectorIndex()
    if os.path.exists(args.index_file) and not args.force_reindex:
        with open(args.index_file, "rb") as f:
            index = pickle.load(f)
        print(f"Loaded index from {args.index_file}")
        print(f"  Current chunks: {index.get_chunk_count()}")
    
    # Ingest documents
    incremental_ingest(source_dir, tracker, index, force_reindex=args.force_reindex)
    
    # Save tracker and index
    with open(args.tracker_file, "wb") as f:
        pickle.dump(tracker, f)
    print(f"Saved tracker to {args.tracker_file}")
    
    with open(args.index_file, "wb") as f:
        pickle.dump(index, f)
    print(f"Saved index to {args.index_file}")
    print(f"  Total chunks: {index.get_chunk_count()}")


if __name__ == "__main__":
    main()
