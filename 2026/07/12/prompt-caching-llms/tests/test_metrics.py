"""
Tests for cache metrics.
"""

import pytest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from cache_metrics import CacheMetrics, calculate_cost_savings


class TestCacheMetrics:
    """Test cache metrics tracking."""
    
    def test_initial_state(self):
        """Test metrics start at zero."""
        metrics = CacheMetrics()
        
        assert metrics.hits == 0
        assert metrics.misses == 0
        assert metrics.hit_ratio() == 0.0
    
    def test_record_hit(self):
        """Test recording cache hits."""
        metrics = CacheMetrics()
        
        metrics.record_hit(latency=0.05, tokens_saved=100, cost_saved=0.001)
        
        assert metrics.hits == 1
        assert metrics.tokens_saved == 100
        assert metrics.cost_saved == 0.001
    
    def test_record_miss(self):
        """Test recording cache misses."""
        metrics = CacheMetrics()
        
        metrics.record_miss(latency=0.5, tokens_processed=100, cost_incurred=0.001)
        
        assert metrics.misses == 1
        assert metrics.tokens_processed == 100
        assert metrics.cost_incurred == 0.001
    
    def test_hit_ratio_calculation(self):
        """Test hit ratio calculation."""
        metrics = CacheMetrics()
        
        # 3 hits, 2 misses = 60% hit ratio
        for _ in range(3):
            metrics.record_hit(0.05, 100, 0.001)
        for _ in range(2):
            metrics.record_miss(0.5, 100, 0.001)
        
        assert metrics.hit_ratio() == 0.6
    
    def test_avg_latencies(self):
        """Test average latency calculations."""
        metrics = CacheMetrics()
        
        # Record some hits with different latencies
        metrics.record_hit(0.01, 100, 0.001)
        metrics.record_hit(0.02, 100, 0.001)
        metrics.record_hit(0.03, 100, 0.001)
        
        # Record some misses
        metrics.record_miss(0.5, 100, 0.001)
        metrics.record_miss(0.6, 100, 0.001)
        
        assert metrics.avg_cache_hit_latency() == 0.02
        assert metrics.avg_cache_miss_latency() == 0.55
    
    def test_latency_reduction(self):
        """Test latency reduction calculation."""
        metrics = CacheMetrics()
        
        # Hits average 0.05s, misses average 0.5s
        metrics.record_hit(0.05, 100, 0.001)
        metrics.record_miss(0.5, 100, 0.001)
        
        reduction = metrics.latency_reduction()
        assert reduction == 0.45  # 0.5 - 0.05
        
        reduction_pct = metrics.latency_reduction_percent()
        assert reduction_pct == 90.0  # (0.45 / 0.5) * 100
    
    def test_tokens_saved_percent(self):
        """Test tokens saved percentage."""
        metrics = CacheMetrics()
        
        # Save 300 tokens, process 100 tokens
        metrics.record_hit(0.05, 300, 0.003)
        metrics.record_miss(0.5, 100, 0.001)
        
        assert metrics.tokens_saved_percent() == 75.0  # 300 / 400
    
    def test_cost_without_cache(self):
        """Test hypothetical cost without cache."""
        metrics = CacheMetrics()
        
        # 3 hits at $0.001 each (if not cached)
        # 2 misses at $0.001 each
        for _ in range(3):
            metrics.record_hit(0.05, 100, 0.0009)  # Saved $0.0009 each
        for _ in range(2):
            metrics.record_miss(0.5, 100, 0.001)
        
        # Without cache, all 5 would cost $0.001
        cost_without = metrics.cost_without_cache()
        assert cost_without == pytest.approx(0.005, rel=0.01)
    
    def test_report_structure(self):
        """Test report contains expected fields."""
        metrics = CacheMetrics()
        metrics.record_hit(0.05, 100, 0.001)
        metrics.record_miss(0.5, 100, 0.001)
        
        report = metrics.report()
        
        expected_keys = [
            "hits", "misses", "total_requests", "hit_ratio",
            "avg_cache_hit_latency_ms", "avg_cache_miss_latency_ms",
            "latency_reduction_ms", "latency_reduction_percent",
            "tokens_saved", "tokens_processed", "total_tokens",
            "tokens_saved_percent", "cost_saved_usd", "cost_incurred_usd",
            "total_cost_usd", "cost_without_cache_usd", "cost_savings_percent",
            "uptime_seconds", "requests_per_second"
        ]
        
        for key in expected_keys:
            assert key in report


class TestCostSavingsCalculation:
    """Test cost savings calculations."""
    
    def test_basic_calculation(self):
        """Test basic cost savings calculation."""
        result = calculate_cost_savings(
            requests_per_day=1000,
            avg_prompt_tokens=500,
            cache_hit_ratio=0.5,
            cost_per_1k_tokens=0.01
        )
        
        assert "daily_cost_without_cache" in result
        assert "daily_cost_with_cache" in result
        assert "daily_savings" in result
        assert result["daily_savings"] > 0
    
    def test_zero_hit_ratio(self):
        """Test with zero cache hits."""
        result = calculate_cost_savings(
            requests_per_day=1000,
            avg_prompt_tokens=500,
            cache_hit_ratio=0.0,
            cost_per_1k_tokens=0.01
        )
        
        # No cache, costs should be equal
        assert result["daily_cost_without_cache"] == result["daily_cost_with_cache"]
        assert result["daily_savings"] == 0
    
    def test_perfect_hit_ratio(self):
        """Test with 100% cache hits."""
        result = calculate_cost_savings(
            requests_per_day=1000,
            avg_prompt_tokens=500,
            cache_hit_ratio=1.0,
            cost_per_1k_tokens=0.01
        )
        
        # All hits at 10% cost = 90% savings
        assert result["savings_percent"] == pytest.approx(90.0, rel=0.01)
    
    def test_monthly_and_yearly(self):
        """Test monthly and yearly projections."""
        result = calculate_cost_savings(
            requests_per_day=1000,
            avg_prompt_tokens=500,
            cache_hit_ratio=0.7,
            cost_per_1k_tokens=0.01
        )
        
        assert result["monthly_savings"] == result["daily_savings"] * 30
        assert result["yearly_savings"] == result["daily_savings"] * 365


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
