"""Token counting, cost estimation, and logging"""

import tiktoken
import json
from datetime import datetime
from typing import Dict, List, Optional


def count_tokens(text: str, encoding_name: str = "cl100k_base") -> int:
    """Count tokens in text."""
    encoding = tiktoken.get_encoding(encoding_name)
    return len(encoding.encode(text))


def estimate_cost(
    prompt_tokens: int,
    completion_tokens: int,
    model: str = "gpt-4"
) -> float:
    """
    Estimate cost for API call.
    
    Pricing (as of 2024, adjust for current rates):
    - GPT-4: $0.03/1k prompt tokens, $0.06/1k completion tokens
    - GPT-3.5 Turbo: $0.0015/1k prompt tokens, $0.002/1k completion tokens
    - GPT-4 Turbo: $0.01/1k prompt tokens, $0.03/1k completion tokens
    """
    pricing = {
        "gpt-4": {"prompt": 0.03, "completion": 0.06},
        "gpt-4-turbo": {"prompt": 0.01, "completion": 0.03},
        "gpt-3.5-turbo": {"prompt": 0.0015, "completion": 0.002}
    }
    
    if model not in pricing:
        # Default to GPT-4 pricing
        model = "gpt-4"
    
    cost = (
        (prompt_tokens / 1000) * pricing[model]["prompt"] +
        (completion_tokens / 1000) * pricing[model]["completion"]
    )
    
    return cost


class RAGLogger:
    """Logger for RAG requests"""
    
    def __init__(self, log_file: str = "rag_logs.jsonl"):
        self.log_file = log_file
    
    def log_request(
        self,
        query: str,
        retrieved_chunks: List[Dict],
        response: str,
        token_counts: Dict[str, int],
        cost: float,
        latency: float,
        metadata: Optional[Dict] = None
    ):
        """Log a RAG request."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "query": query,
            "num_chunks": len(retrieved_chunks),
            "chunk_tokens": sum(count_tokens(chunk["text"]) for chunk in retrieved_chunks),
            "response_tokens": token_counts.get("completion_tokens", 0),
            "total_tokens": token_counts.get("total_tokens", 0),
            "cost": cost,
            "latency_ms": latency * 1000,
            "metadata": metadata or {}
        }
        
        with open(self.log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
    
    def get_stats(self) -> Dict:
        """Get statistics from logs."""
        stats = {
            "total_requests": 0,
            "total_tokens": 0,
            "total_cost": 0.0,
            "avg_latency_ms": 0.0
        }
        
        try:
            with open(self.log_file, "r") as f:
                latencies = []
                for line in f:
                    entry = json.loads(line)
                    stats["total_requests"] += 1
                    stats["total_tokens"] += entry.get("total_tokens", 0)
                    stats["total_cost"] += entry.get("cost", 0.0)
                    latencies.append(entry.get("latency_ms", 0.0))
                
                if latencies:
                    stats["avg_latency_ms"] = sum(latencies) / len(latencies)
        except FileNotFoundError:
            pass
        
        return stats

