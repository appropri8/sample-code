"""Tests for A/B testing"""

import pytest
from src.ab_testing import route_to_variant, get_or_assign_variant


def test_route_to_variant():
    """Test variant routing."""
    variants = {"v1": 0.5, "v2": 0.5}
    
    # Same user should get same variant
    user_id = "user_123"
    variant1 = route_to_variant(user_id, variants)
    variant2 = route_to_variant(user_id, variants)
    
    assert variant1 == variant2
    assert variant1 in ["v1", "v2"]


def test_route_to_variant_weights():
    """Test variant routing with different weights."""
    variants = {"v1": 0.8, "v2": 0.2}
    
    # Test multiple users
    results = {"v1": 0, "v2": 0}
    for i in range(100):
        user_id = f"user_{i}"
        variant = route_to_variant(user_id, variants)
        results[variant] += 1
    
    # v1 should have more assignments (approximately 80%)
    assert results["v1"] > results["v2"]


def test_route_to_variant_consistency():
    """Test that routing is consistent for same user."""
    variants = {"v1": 0.5, "v2": 0.5}
    user_id = "user_456"
    
    # Route multiple times
    variants_assigned = [route_to_variant(user_id, variants) for _ in range(10)]
    
    # All should be the same
    assert len(set(variants_assigned)) == 1

