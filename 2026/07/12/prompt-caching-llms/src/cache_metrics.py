"""
Cache metrics and monitoring.

Track cache effectiveness with multiple metrics:
- Hit ratio
- Cost savings
- Latency reduction
- Token reduction
"""

import time
from typing import List, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class CacheMetrics:
    """Track cache performance metrics."""
    
    # Counters
    hits: int = 0
    misses: int = 0
    
    # Latency tracking
    cache_hit_latencies: List[float] = field(default_factory=list)
    cache_miss_latencies: List[float] = field(default_factory=list)
    
    # Token tracking
    tokens_saved: int = 0
    tokens_processed: int = 0
    
    # Cost tracking (USD)
    cost_saved: float = 0.0
    cost_incurred: float = 0.0
    
    # Timestamps
    start_time: datetime = field(default_factory=datetime.now)
    
    def record_hit(self, latency: float, tokens_saved: int, cost_saved: float):
        """
        Record a cache hit.
        
        Args:
            latency: Request latency in seconds
            tokens_saved: Number of tokens not processed
            cost_saved: Cost saved in USD
        """
        self.hits += 1
        self.cache_hit_latencies.append(latency)
        self.tokens_saved += tokens_saved
        self.cost_saved += cost_saved
    
    def record_miss(self, latency: float, tokens_processed: int, cost_incurred: float):
        """
        Record a cache miss.
        
        Args:
            latency: Request latency in seconds
            tokens_processed: Number of tokens processed
            cost_incurred: Cost incurred in USD
        """
        self.misses += 1
        self.cache_miss_latencies.append(latency)
        self.tokens_processed += tokens_processed
        self.cost_incurred += cost_incurred
    
    def hit_ratio(self) -> float:
        """Calculate cache hit ratio."""
        total = self.hits + self.misses
        if total == 0:
            return 0.0
        return self.hits / total
    
    def avg_cache_hit_latency(self) -> float:
        """Average latency for cache hits."""
        if not self.cache_hit_latencies:
            return 0.0
        return sum(self.cache_hit_latencies) / len(self.cache_hit_latencies)
    
    def avg_cache_miss_latency(self) -> float:
        """Average latency for cache misses."""
        if not self.cache_miss_latencies:
            return 0.0
        return sum(self.cache_miss_latencies) / len(self.cache_miss_latencies)
    
    def latency_reduction(self) -> float:
        """Calculate latency reduction from caching."""
        miss_latency = self.avg_cache_miss_latency()
        hit_latency = self.avg_cache_hit_latency()
        
        if miss_latency == 0:
            return 0.0
        
        return miss_latency - hit_latency
    
    def latency_reduction_percent(self) -> float:
        """Calculate latency reduction as percentage."""
        miss_latency = self.avg_cache_miss_latency()
        
        if miss_latency == 0:
            return 0.0
        
        reduction = self.latency_reduction()
        return (reduction / miss_latency) * 100
    
    def total_cost(self) -> float:
        """Total cost (saved + incurred)."""
        return self.cost_saved + self.cost_incurred
    
    def cost_without_cache(self) -> float:
        """Hypothetical cost without caching."""
        # If we hadn't cached, all requests would have incurred full cost
        if self.misses == 0:
            return self.cost_incurred
        
        avg_cost_per_miss = self.cost_incurred / self.misses if self.misses > 0 else 0
        return avg_cost_per_miss * (self.hits + self.misses)
    
    def cost_savings_percent(self) -> float:
        """Calculate cost savings as percentage."""
        cost_without = self.cost_without_cache()
        
        if cost_without == 0:
            return 0.0
        
        actual_cost = self.cost_incurred
        savings = cost_without - actual_cost
        return (savings / cost_without) * 100
    
    def tokens_saved_percent(self) -> float:
        """Calculate percentage of tokens saved."""
        total_tokens = self.tokens_saved + self.tokens_processed
        
        if total_tokens == 0:
            return 0.0
        
        return (self.tokens_saved / total_tokens) * 100
    
    def uptime_seconds(self) -> float:
        """Seconds since metrics started."""
        return (datetime.now() - self.start_time).total_seconds()
    
    def requests_per_second(self) -> float:
        """Calculate requests per second."""
        uptime = self.uptime_seconds()
        if uptime == 0:
            return 0.0
        
        total_requests = self.hits + self.misses
        return total_requests / uptime
    
    def report(self) -> dict:
        """Generate comprehensive metrics report."""
        return {
            # Hit/miss stats
            "hits": self.hits,
            "misses": self.misses,
            "total_requests": self.hits + self.misses,
            "hit_ratio": self.hit_ratio(),
            
            # Latency stats
            "avg_cache_hit_latency_ms": self.avg_cache_hit_latency() * 1000,
            "avg_cache_miss_latency_ms": self.avg_cache_miss_latency() * 1000,
            "latency_reduction_ms": self.latency_reduction() * 1000,
            "latency_reduction_percent": self.latency_reduction_percent(),
            
            # Token stats
            "tokens_saved": self.tokens_saved,
            "tokens_processed": self.tokens_processed,
            "total_tokens": self.tokens_saved + self.tokens_processed,
            "tokens_saved_percent": self.tokens_saved_percent(),
            
            # Cost stats
            "cost_saved_usd": self.cost_saved,
            "cost_incurred_usd": self.cost_incurred,
            "total_cost_usd": self.total_cost(),
            "cost_without_cache_usd": self.cost_without_cache(),
            "cost_savings_percent": self.cost_savings_percent(),
            
            # Performance
            "uptime_seconds": self.uptime_seconds(),
            "requests_per_second": self.requests_per_second(),
        }
    
    def print_report(self):
        """Print formatted metrics report."""
        report = self.report()
        
        print("=== Cache Metrics Report ===\n")
        
        print("Request Statistics:")
        print(f"  Total Requests: {report['total_requests']}")
        print(f"  Cache Hits: {report['hits']}")
        print(f"  Cache Misses: {report['misses']}")
        print(f"  Hit Ratio: {report['hit_ratio']:.1%}")
        print()
        
        print("Latency Statistics:")
        print(f"  Avg Hit Latency: {report['avg_cache_hit_latency_ms']:.1f}ms")
        print(f"  Avg Miss Latency: {report['avg_cache_miss_latency_ms']:.1f}ms")
        print(f"  Latency Reduction: {report['latency_reduction_ms']:.1f}ms ({report['latency_reduction_percent']:.1f}%)")
        print()
        
        print("Token Statistics:")
        print(f"  Tokens Saved: {report['tokens_saved']:,}")
        print(f"  Tokens Processed: {report['tokens_processed']:,}")
        print(f"  Total Tokens: {report['total_tokens']:,}")
        print(f"  Tokens Saved: {report['tokens_saved_percent']:.1f}%")
        print()
        
        print("Cost Statistics:")
        print(f"  Cost Incurred: ${report['cost_incurred_usd']:.4f}")
        print(f"  Cost Without Cache: ${report['cost_without_cache_usd']:.4f}")
        print(f"  Cost Savings: ${report['cost_without_cache_usd'] - report['cost_incurred_usd']:.4f} ({report['cost_savings_percent']:.1f}%)")
        print()
        
        print("Performance:")
        print(f"  Uptime: {report['uptime_seconds']:.1f}s")
        print(f"  Requests/sec: {report['requests_per_second']:.2f}")


def demo_metrics():
    """Demonstrate metrics tracking."""
    print("=== Cache Metrics Demo ===\n")
    
    metrics = CacheMetrics()
    
    # Simulate requests
    print("Simulating requests...\n")
    
    # Request 1: Cache miss
    time.sleep(0.01)  # Simulate processing
    metrics.record_miss(
        latency=0.5,
        tokens_processed=500,
        cost_incurred=0.005
    )
    
    # Request 2: Cache hit
    time.sleep(0.001)  # Simulate cache lookup
    metrics.record_hit(
        latency=0.05,
        tokens_saved=500,
        cost_saved=0.0045  # 90% savings
    )
    
    # Request 3: Cache hit
    time.sleep(0.001)
    metrics.record_hit(
        latency=0.04,
        tokens_saved=500,
        cost_saved=0.0045
    )
    
    # Request 4: Cache miss
    time.sleep(0.01)
    metrics.record_miss(
        latency=0.52,
        tokens_processed=500,
        cost_incurred=0.005
    )
    
    # Request 5: Cache hit
    time.sleep(0.001)
    metrics.record_hit(
        latency=0.06,
        tokens_saved=500,
        cost_saved=0.0045
    )
    
    # Print report
    metrics.print_report()


def calculate_cost_savings(
    requests_per_day: int,
    avg_prompt_tokens: int,
    cache_hit_ratio: float,
    cost_per_1k_tokens: float
):
    """
    Calculate projected cost savings.
    
    Args:
        requests_per_day: Daily request volume
        avg_prompt_tokens: Average tokens per prompt
        cache_hit_ratio: Expected cache hit ratio (0-1)
        cost_per_1k_tokens: Cost per 1K tokens in USD
        
    Returns:
        Dictionary with cost projections
    """
    # Without cache
    daily_tokens = requests_per_day * avg_prompt_tokens
    daily_cost_without_cache = (daily_tokens / 1000) * cost_per_1k_tokens
    
    # With cache (assuming hits cost 10% of normal)
    cache_hit_cost = (
        requests_per_day * cache_hit_ratio * avg_prompt_tokens / 1000
    ) * cost_per_1k_tokens * 0.1
    
    cache_miss_cost = (
        requests_per_day * (1 - cache_hit_ratio) * avg_prompt_tokens / 1000
    ) * cost_per_1k_tokens
    
    daily_cost_with_cache = cache_hit_cost + cache_miss_cost
    
    # Savings
    daily_savings = daily_cost_without_cache - daily_cost_with_cache
    monthly_savings = daily_savings * 30
    yearly_savings = daily_savings * 365
    
    return {
        "requests_per_day": requests_per_day,
        "avg_prompt_tokens": avg_prompt_tokens,
        "cache_hit_ratio": cache_hit_ratio,
        "cost_per_1k_tokens": cost_per_1k_tokens,
        "daily_cost_without_cache": daily_cost_without_cache,
        "daily_cost_with_cache": daily_cost_with_cache,
        "daily_savings": daily_savings,
        "monthly_savings": monthly_savings,
        "yearly_savings": yearly_savings,
        "savings_percent": (daily_savings / daily_cost_without_cache) * 100
    }


def demo_cost_projections():
    """Demonstrate cost projections."""
    print("\n\n=== Cost Projections Demo ===\n")
    
    scenarios = [
        {
            "name": "Small App",
            "requests_per_day": 1_000,
            "avg_prompt_tokens": 500,
            "cache_hit_ratio": 0.6,
            "cost_per_1k_tokens": 0.01
        },
        {
            "name": "Medium App",
            "requests_per_day": 10_000,
            "avg_prompt_tokens": 500,
            "cache_hit_ratio": 0.7,
            "cost_per_1k_tokens": 0.01
        },
        {
            "name": "Large App",
            "requests_per_day": 100_000,
            "avg_prompt_tokens": 1000,
            "cache_hit_ratio": 0.8,
            "cost_per_1k_tokens": 0.01
        },
    ]
    
    for scenario in scenarios:
        print(f"Scenario: {scenario['name']}")
        print(f"  Requests/day: {scenario['requests_per_day']:,}")
        print(f"  Avg tokens: {scenario['avg_prompt_tokens']}")
        print(f"  Hit ratio: {scenario['cache_hit_ratio']:.0%}")
        
        result = calculate_cost_savings(**scenario)
        
        print(f"\nCosts:")
        print(f"  Without cache: ${result['daily_cost_without_cache']:.2f}/day")
        print(f"  With cache: ${result['daily_cost_with_cache']:.2f}/day")
        print(f"\nSavings:")
        print(f"  Daily: ${result['daily_savings']:.2f} ({result['savings_percent']:.1f}%)")
        print(f"  Monthly: ${result['monthly_savings']:.2f}")
        print(f"  Yearly: ${result['yearly_savings']:.2f}")
        print("\n" + "="*50 + "\n")


if __name__ == "__main__":
    demo_metrics()
    demo_cost_projections()
