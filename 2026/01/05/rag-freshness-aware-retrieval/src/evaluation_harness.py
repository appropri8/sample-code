"""Evaluation harness for freshness-aware RAG."""

import argparse
import json
import pickle
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict
from collections import defaultdict

from src.vector_index import VectorIndex
from src.freshness_retrieval import retrieve_with_freshness


class FreshnessMetrics:
    """Track freshness evaluation metrics."""
    
    def __init__(self):
        self.total_queries = 0
        self.correct_citations = 0
        self.stale_citations = 0
        self.top_k_hits = 0
        self.answer_changes = 0
        self.queries_by_type = defaultdict(int)
        self.errors_by_type = defaultdict(int)
    
    def record_citation(
        self,
        retrieved_doc_id: str,
        expected_doc_id: str,
        is_stale: bool,
        query_type: str = "general"
    ):
        """Record citation accuracy."""
        self.total_queries += 1
        self.queries_by_type[query_type] += 1
        
        if retrieved_doc_id == expected_doc_id:
            self.correct_citations += 1
        elif is_stale:
            self.stale_citations += 1
            self.errors_by_type[query_type] += 1
    
    def record_top_k_hit(self, expected_doc_id: str, retrieved_doc_ids: List[str]):
        """Record if expected doc is in top-k."""
        if expected_doc_id in retrieved_doc_ids:
            self.top_k_hits += 1
    
    def record_answer_change(self, old_answer: str, new_answer: str):
        """Record when answer changes after doc update."""
        if old_answer != new_answer:
            self.answer_changes += 1
    
    def get_report(self) -> Dict:
        """Get metrics report."""
        if self.total_queries == 0:
            return {"error": "No queries processed"}
        
        return {
            "total_queries": self.total_queries,
            "citation_accuracy": self.correct_citations / self.total_queries,
            "stale_citation_rate": self.stale_citations / self.total_queries,
            "top_k_hit_rate": self.top_k_hits / self.total_queries,
            "answer_change_rate": self.answer_changes / self.total_queries,
            "queries_by_type": dict(self.queries_by_type),
            "errors_by_type": dict(self.errors_by_type)
        }


def load_test_set(test_set_path: Path) -> List[Dict]:
    """Load test set from JSONL file.
    
    Args:
        test_set_path: Path to JSONL file
    
    Returns:
        List of test cases
    """
    test_cases = []
    
    with open(test_set_path, "r") as f:
        for line in f:
            if line.strip():
                test_cases.append(json.loads(line))
    
    return test_cases


def is_stale(published_at: datetime, threshold_days: int = 30) -> bool:
    """Check if document is stale.
    
    Args:
        published_at: Publication date
        threshold_days: Days after which document is considered stale
    
    Returns:
        True if stale
    """
    age_days = (datetime.now() - published_at).days
    return age_days > threshold_days


def evaluate(
    index: VectorIndex,
    test_cases: List[Dict],
    top_k: int = 5,
    stale_threshold_days: int = 30
) -> FreshnessMetrics:
    """Evaluate retrieval on test set.
    
    Args:
        index: Vector index
        test_cases: List of test cases
        top_k: Number of results to retrieve
        stale_threshold_days: Days after which document is stale
    
    Returns:
        FreshnessMetrics object
    """
    metrics = FreshnessMetrics()
    
    for test_case in test_cases:
        query = test_case["query"]
        expected_doc_id = test_case["expected_doc_id"]
        query_type = test_case.get("query_type", "general")
        
        # Retrieve results
        results = retrieve_with_freshness(query, index, top_k=top_k)
        
        if not results:
            metrics.record_citation("", expected_doc_id, False, query_type)
            continue
        
        # Get top result
        top_result = results[0]
        retrieved_doc_id = top_result.doc_id
        
        # Check if stale
        is_stale_result = is_stale(top_result.published_at, stale_threshold_days)
        
        # Record metrics
        metrics.record_citation(retrieved_doc_id, expected_doc_id, is_stale_result, query_type)
        
        # Check top-k hit
        retrieved_doc_ids = [r.doc_id for r in results]
        metrics.record_top_k_hit(expected_doc_id, retrieved_doc_ids)
    
    return metrics


def print_report(metrics: FreshnessMetrics):
    """Print evaluation report.
    
    Args:
        metrics: FreshnessMetrics object
    """
    report = metrics.get_report()
    
    if "error" in report:
        print(f"Error: {report['error']}")
        return
    
    print("\n" + "="*60)
    print("EVALUATION REPORT")
    print("="*60)
    print(f"\nTotal Queries: {report['total_queries']}")
    print(f"\nCitation Accuracy: {report['citation_accuracy']:.2%}")
    print(f"Stale Citation Rate: {report['stale_citation_rate']:.2%}")
    print(f"Top-K Hit Rate: {report['top_k_hit_rate']:.2%}")
    print(f"Answer Change Rate: {report['answer_change_rate']:.2%}")
    
    if report['queries_by_type']:
        print(f"\nQueries by Type:")
        for query_type, count in report['queries_by_type'].items():
            error_count = report['errors_by_type'].get(query_type, 0)
            error_rate = error_count / count if count > 0 else 0
            print(f"  {query_type}: {count} queries, {error_rate:.2%} error rate")
    
    print("="*60 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Evaluate freshness-aware retrieval")
    parser.add_argument(
        "--test-set",
        type=str,
        required=True,
        help="Path to JSONL test set file"
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
        help="Number of results to retrieve"
    )
    parser.add_argument(
        "--stale-threshold-days",
        type=int,
        default=30,
        help="Days after which document is considered stale"
    )
    
    args = parser.parse_args()
    
    # Load test set
    test_set_path = Path(args.test_set)
    if not test_set_path.exists():
        print(f"Error: {args.test_set} does not exist")
        return
    
    test_cases = load_test_set(test_set_path)
    print(f"Loaded {len(test_cases)} test cases")
    
    # Load index
    index_path = Path(args.index_file)
    if not index_path.exists():
        print(f"Error: {args.index_file} does not exist")
        print("Run incremental_ingestion.py first to create the index")
        return
    
    with open(args.index_file, "rb") as f:
        index = pickle.load(f)
    
    print(f"Loaded index with {index.get_chunk_count()} chunks")
    
    # Evaluate
    print(f"\nEvaluating with top_k={args.top_k}, stale_threshold={args.stale_threshold_days} days...")
    metrics = evaluate(index, test_cases, top_k=args.top_k, stale_threshold_days=args.stale_threshold_days)
    
    # Print report
    print_report(metrics)


if __name__ == "__main__":
    main()
