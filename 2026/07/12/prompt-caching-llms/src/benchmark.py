"""
Benchmark different caching strategies.

Compare:
1. No cache
2. Response cache
3. Prompt cache (simulated)
"""

import time
import random
from typing import List, Tuple
from simple_response_cache import SimpleResponseCache


def mock_llm_call(prompt: str, cache_type: str = "none") -> Tuple[str, float]:
    """
    Mock LLM call with different cache behaviors.
    
    Args:
        prompt: The prompt
        cache_type: "none", "response", or "prompt"
        
    Returns:
        Tuple of (response, latency_seconds)
    """
    if cache_type == "none":
        # Full processing
        time.sleep(0.5)
        return f"Response to: {prompt[:30]}...", 0.5
    
    elif cache_type == "response":
        # Response cache - instant for exact match
        time.sleep(0.001)
        return f"Cached response to: {prompt[:30]}...", 0.001
    
    elif cache_type == "prompt":
        # Prompt cache - faster but not instant (partial reuse)
        # Simulate 80% time savings
        time.sleep(0.1)
        return f"Prompt-cached response to: {prompt[:30]}...", 0.1
    
    return "", 0.0


def generate_test_queries(num_queries: int, num_unique: int) -> List[str]:
    """
    Generate test queries with some repetition.
    
    Args:
        num_queries: Total number of queries
        num_unique: Number of unique queries
        
    Returns:
        List of queries
    """
    unique_queries = [
        f"What is topic number {i}?" for i in range(num_unique)
    ]
    
    # Generate queries with repetition
    queries = []
    for _ in range(num_queries):
        queries.append(random.choice(unique_queries))
    
    return queries


def benchmark_no_cache(queries: List[str]) -> dict:
    """Benchmark with no caching."""
    print("Running benchmark: No Cache")
    
    total_latency = 0.0
    total_cost = 0.0
    tokens_per_request = 100
    cost_per_1k = 0.01
    
    for query in queries:
        response, latency = mock_llm_call(query, "none")
        total_latency += latency
        total_cost += (tokens_per_request / 1000) * cost_per_1k
    
    return {
        "name": "No Cache",
        "total_requests": len(queries),
        "total_latency": total_latency,
        "avg_latency": total_latency / len(queries),
        "total_cost": total_cost,
        "hits": 0,
        "misses": len(queries),
        "hit_ratio": 0.0
    }


def benchmark_response_cache(queries: List[str]) -> dict:
    """Benchmark with response caching."""
    print("Running benchmark: Response Cache")
    
    cache = {}
    hits = 0
    misses = 0
    total_latency = 0.0
    total_cost = 0.0
    tokens_per_request = 100
    cost_per_1k = 0.01
    
    for query in queries:
        if query in cache:
            # Cache hit
            response, latency = mock_llm_call(query, "response")
            hits += 1
            # Cache hits cost 10% of normal
            total_cost += (tokens_per_request / 1000) * cost_per_1k * 0.1
        else:
            # Cache miss
            response, latency = mock_llm_call(query, "none")
            cache[query] = response
            misses += 1
            total_cost += (tokens_per_request / 1000) * cost_per_1k
        
        total_latency += latency
    
    return {
        "name": "Response Cache",
        "total_requests": len(queries),
        "total_latency": total_latency,
        "avg_latency": total_latency / len(queries),
        "total_cost": total_cost,
        "hits": hits,
        "misses": misses,
        "hit_ratio": hits / len(queries)
    }


def benchmark_prompt_cache(queries: List[str]) -> dict:
    """Benchmark with prompt caching (simulated)."""
    print("Running benchmark: Prompt Cache (Simulated)")
    
    # Simulate prompt cache by tracking prefixes
    # In reality, this would be provider-managed
    prefix_cache = set()
    hits = 0
    misses = 0
    total_latency = 0.0
    total_cost = 0.0
    tokens_per_request = 100
    cost_per_1k = 0.01
    
    for query in queries:
        # Simulate: first 50 chars are stable system prompt
        prefix = query[:50] if len(query) > 50 else query
        
        if prefix in prefix_cache:
            # Prefix cached - faster processing
            response, latency = mock_llm_call(query, "prompt")
            hits += 1
            # Prompt cache saves ~50% of input tokens
            total_cost += (tokens_per_request / 1000) * cost_per_1k * 0.5
        else:
            # New prefix - full processing
            response, latency = mock_llm_call(query, "none")
            prefix_cache.add(prefix)
            misses += 1
            total_cost += (tokens_per_request / 1000) * cost_per_1k
        
        total_latency += latency
    
    return {
        "name": "Prompt Cache",
        "total_requests": len(queries),
        "total_latency": total_latency,
        "avg_latency": total_latency / len(queries),
        "total_cost": total_cost,
        "hits": hits,
        "misses": misses,
        "hit_ratio": hits / len(queries)
    }


def print_comparison(results: List[dict]):
    """Print comparison table."""
    print("\n" + "="*80)
    print("BENCHMARK RESULTS COMPARISON")
    print("="*80 + "\n")
    
    # Header
    print(f"{'Strategy':<20} {'Requests':<12} {'Hits':<10} {'Hit Ratio':<12} {'Avg Latency':<15} {'Total Cost':<12}")
    print("-"*80)
    
    # Data rows
    for result in results:
        print(
            f"{result['name']:<20} "
            f"{result['total_requests']:<12} "
            f"{result['hits']:<10} "
            f"{result['hit_ratio']:<12.1%} "
            f"{result['avg_latency']*1000:<15.1f}ms "
            f"${result['total_cost']:<11.4f}"
        )
    
    print("-"*80)
    
    # Calculate savings compared to no cache
    baseline = results[0]  # No cache
    
    print("\nSavings vs No Cache:")
    for result in results[1:]:
        latency_savings = baseline['avg_latency'] - result['avg_latency']
        latency_savings_pct = (latency_savings / baseline['avg_latency']) * 100
        
        cost_savings = baseline['total_cost'] - result['total_cost']
        cost_savings_pct = (cost_savings / baseline['total_cost']) * 100
        
        print(f"\n{result['name']}:")
        print(f"  Latency: -{latency_savings*1000:.1f}ms (-{latency_savings_pct:.1f}%)")
        print(f"  Cost: -${cost_savings:.4f} (-{cost_savings_pct:.1f}%)")


def run_benchmark():
    """Run complete benchmark."""
    print("=== Cache Strategy Benchmark ===\n")
    
    # Generate test queries
    # 100 requests, 20 unique queries (80% will be cache hits)
    queries = generate_test_queries(num_queries=100, num_unique=20)
    
    print(f"Generated {len(queries)} queries ({len(set(queries))} unique)\n")
    
    # Run benchmarks
    results = []
    
    results.append(benchmark_no_cache(queries))
    print()
    
    results.append(benchmark_response_cache(queries))
    print()
    
    results.append(benchmark_prompt_cache(queries))
    print()
    
    # Print comparison
    print_comparison(results)


def run_scalability_test():
    """Test how caching scales with volume."""
    print("\n\n=== Scalability Test ===\n")
    
    volumes = [100, 500, 1000, 5000]
    unique_ratio = 0.2  # 20% unique queries
    
    print(f"{'Volume':<12} {'No Cache':<20} {'Response Cache':<20} {'Savings':<15}")
    print("-"*70)
    
    for volume in volumes:
        unique_count = int(volume * unique_ratio)
        queries = generate_test_queries(volume, unique_count)
        
        # Quick benchmark (without printing)
        no_cache_result = benchmark_no_cache(queries)
        response_cache_result = benchmark_response_cache(queries)
        
        savings = no_cache_result['total_cost'] - response_cache_result['total_cost']
        savings_pct = (savings / no_cache_result['total_cost']) * 100
        
        print(
            f"{volume:<12} "
            f"${no_cache_result['total_cost']:<19.4f} "
            f"${response_cache_result['total_cost']:<19.4f} "
            f"${savings:.4f} ({savings_pct:.1f}%)"
        )


if __name__ == "__main__":
    run_benchmark()
    run_scalability_test()
