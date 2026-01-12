"""Reranking with freshness scores."""

import math
from datetime import datetime, timedelta
from typing import List
from src.vector_index import SearchResult


def compute_freshness_score(
    published_at: datetime,
    decay_half_life_days: int = 30
) -> float:
    """Compute freshness score using exponential decay.
    
    Args:
        published_at: When the document was published
        decay_half_life_days: Days until score halves (default 30)
    
    Returns:
        Freshness score between 0.0 and 1.0
    """
    age_days = (datetime.now() - published_at).days
    
    if age_days < 0:
        return 1.0  # Future dates (shouldn't happen)
    
    # Exponential decay: score halves every decay_half_life_days
    score = math.exp(-age_days * math.log(2) / decay_half_life_days)
    return max(0.0, min(1.0, score))


def compute_source_priority(source_type: str) -> float:
    """Compute source priority score.
    
    Args:
        source_type: Type of source (policy, official_docs, wiki, etc.)
    
    Returns:
        Priority score between 0.0 and 1.0
    """
    priorities = {
        "policy": 1.0,
        "official_docs": 0.9,
        "documentation": 0.8,
        "wiki": 0.7,
        "blog": 0.6,
        "forum": 0.5,
        "product": 0.8
    }
    return priorities.get(source_type, 0.5)


def is_time_based_query(query: str) -> bool:
    """Check if query is time-sensitive.
    
    Args:
        query: User query
    
    Returns:
        True if query is time-sensitive
    """
    time_indicators = [
        "as of", "current", "latest", "recent", "updated",
        "this month", "this year", "now", "today"
    ]
    query_lower = query.lower()
    return any(indicator in query_lower for indicator in time_indicators)


def rerank_with_freshness(
    results: List[SearchResult],
    query: str = "",
    relevance_weight: float = 0.6,
    freshness_weight: float = 0.3,
    source_weight: float = 0.1,
    decay_half_life_days: int = 30
) -> List[SearchResult]:
    """Rerank results considering relevance, freshness, and source.
    
    Args:
        results: Initial search results
        query: Original query (for time-based detection)
        relevance_weight: Weight for relevance score (default 0.6)
        freshness_weight: Weight for freshness score (default 0.3)
        source_weight: Weight for source priority (default 0.1)
        decay_half_life_days: Days until freshness score halves
    
    Returns:
        Reranked results with combined_score set
    """
    # Adjust weights for time-based queries
    if is_time_based_query(query):
        relevance_weight = 0.4
        freshness_weight = 0.5  # Higher freshness weight
        source_weight = 0.1
    
    # Ensure weights sum to 1.0
    total_weight = relevance_weight + freshness_weight + source_weight
    if total_weight != 1.0:
        relevance_weight /= total_weight
        freshness_weight /= total_weight
        source_weight /= total_weight
    
    # Compute combined scores
    for result in results:
        # Normalize relevance score (assume 0-1 range, but handle negative)
        relevance = max(0.0, result.relevance_score)
        
        # Compute freshness
        freshness = compute_freshness_score(
            result.published_at,
            decay_half_life_days=decay_half_life_days
        )
        
        # Compute source priority
        source_priority = compute_source_priority(result.source_type)
        
        # Combined score
        combined_score = (
            relevance_weight * relevance +
            freshness_weight * freshness +
            source_weight * source_priority
        )
        
        result.combined_score = combined_score
    
    # Sort by combined score
    return sorted(results, key=lambda x: x.combined_score, reverse=True)


def extract_relevant_snippet(text: str, query: str, max_length: int = 200) -> str:
    """Extract short relevant snippet from text.
    
    Args:
        text: Full text
        query: Query terms
        max_length: Maximum snippet length
    
    Returns:
        Short relevant snippet
    """
    # Find sentences containing query terms
    sentences = text.split('.')
    query_terms = set(query.lower().split())
    
    relevant_sentences = []
    for sentence in sentences:
        sentence_lower = sentence.lower()
        if any(term in sentence_lower for term in query_terms):
            relevant_sentences.append(sentence.strip())
    
    # Combine until we hit max_length
    snippet = ""
    for sentence in relevant_sentences:
        if len(snippet) + len(sentence) > max_length:
            break
        snippet += sentence + ". "
    
    return snippet.strip() if snippet else text[:max_length]
