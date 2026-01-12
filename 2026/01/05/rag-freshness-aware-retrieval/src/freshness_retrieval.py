"""Freshness-aware retrieval with reranking."""

import argparse
import pickle
from pathlib import Path
import numpy as np

from src.vector_index import VectorIndex
from src.reranker import rerank_with_freshness, extract_relevant_snippet


def rewrite_query(query: str) -> str:
    """Rewrite query for better retrieval.
    
    Args:
        query: Original query
    
    Returns:
        Rewritten query
    """
    # Remove common stop words
    stop_words = {"what", "is", "the", "a", "an", "how", "does", "do", "our", "your"}
    words = query.lower().split()
    filtered = [w for w in words if w not in stop_words]
    
    # Keep original if too short after filtering
    if len(filtered) < 2:
        return query
    
    return " ".join(filtered)


def generate_embedding(text: str) -> np.ndarray:
    """Generate embedding for query.
    
    In production, use OpenAI or another embedding API.
    For demo, use random embedding.
    
    Args:
        text: Query text
    
    Returns:
        Embedding vector
    """
    # In production, use OpenAI or another embedding service
    # For demo purposes, use random embedding
    embedding = np.random.rand(1536).astype(np.float32)
    embedding = embedding / np.linalg.norm(embedding)
    return embedding


def retrieve_with_freshness(
    query: str,
    index: VectorIndex,
    top_k: int = 5
) -> list:
    """Retrieve and rerank results with freshness awareness.
    
    Args:
        query: User query
        index: Vector index
        top_k: Number of results to return
    
    Returns:
        List of reranked SearchResult objects
    """
    # Rewrite query
    rewritten = rewrite_query(query)
    print(f"Original query: {query}")
    print(f"Rewritten query: {rewritten}")
    
    # Generate query embedding
    query_embedding = generate_embedding(query)
    
    # Retrieve top N (get more for reranking)
    initial_results = index.search(query_embedding, top_k=top_k * 3)
    
    if not initial_results:
        return []
    
    print(f"\nRetrieved {len(initial_results)} initial results")
    print("Top 3 by relevance:")
    for i, result in enumerate(initial_results[:3], 1):
        print(f"  {i}. {result.doc_id} (relevance={result.relevance_score:.3f}, "
              f"freshness={result.published_at.date()})")
    
    # Rerank with freshness
    reranked = rerank_with_freshness(
        initial_results,
        query=query,
        relevance_weight=0.6,
        freshness_weight=0.3,
        source_weight=0.1
    )
    
    print(f"\nReranked top {top_k} results:")
    for i, result in enumerate(reranked[:top_k], 1):
        print(f"  {i}. {result.doc_id} (combined={result.combined_score:.3f}, "
              f"relevance={result.relevance_score:.3f}, "
              f"published={result.published_at.date()}, "
              f"version={result.version})")
    
    return reranked[:top_k]


def format_answer(query: str, results: list) -> str:
    """Format answer with citations.
    
    Args:
        query: Original query
        results: Retrieved results
    
    Returns:
        Formatted answer with citations
    """
    if not results:
        return "I don't have enough information in the provided sources to answer this question."
    
    # Extract relevant snippets
    snippets = []
    for i, result in enumerate(results, 1):
        snippet = extract_relevant_snippet(result.content, query, max_length=150)
        snippets.append(f"[{i}] {snippet}")
    
    # Generate answer (in production, use LLM)
    # For demo, just format the snippets
    answer = f"Based on the provided sources:\n\n"
    answer += "\n\n".join(snippets)
    answer += f"\n\nSources: {', '.join(f'[{i+1}] {r.doc_id} (v{r.version})' for i, r in enumerate(results))}"
    
    return answer


def main():
    parser = argparse.ArgumentParser(description="Freshness-aware retrieval")
    parser.add_argument(
        "--query",
        type=str,
        required=True,
        help="Query to search for"
    )
    parser.add_argument(
        "--index-file",
        type=str,
        default="index.pkl",
        help="File containing vector index"
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Number of results to return"
    )
    
    args = parser.parse_args()
    
    # Load index
    if not Path(args.index_file).exists():
        print(f"Error: {args.index_file} does not exist")
        print("Run incremental_ingestion.py first to create the index")
        return
    
    with open(args.index_file, "rb") as f:
        index = pickle.load(f)
    
    print(f"Loaded index with {index.get_chunk_count()} chunks\n")
    
    # Retrieve with freshness
    results = retrieve_with_freshness(args.query, index, top_k=args.top_k)
    
    # Format answer
    print("\n" + "="*60)
    answer = format_answer(args.query, results)
    print(answer)
    print("="*60)


if __name__ == "__main__":
    main()
