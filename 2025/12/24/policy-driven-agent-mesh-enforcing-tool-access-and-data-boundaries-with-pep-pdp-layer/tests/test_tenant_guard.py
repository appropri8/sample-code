"""Tests for tenant guard."""
import pytest
from src.tools.tenant_guard import TenantGuard


def test_tenant_guard_allows_matching_tenant():
    """Test tenant guard allows matching tenant."""
    guard = TenantGuard()
    
    safe_params = guard.enforce_tenant_isolation(
        request_tenant_id="acme-corp",
        query_params={"tenant_id": "acme-corp", "limit": 100},
        tool_name="ReadOrders"
    )
    
    assert safe_params["tenant_id"] == "acme-corp"


def test_tenant_guard_denies_mismatched_tenant():
    """Test tenant guard denies mismatched tenant."""
    guard = TenantGuard()
    
    with pytest.raises(PermissionError, match="Cross-tenant access denied"):
        guard.enforce_tenant_isolation(
            request_tenant_id="acme-corp",
            query_params={"tenant_id": "competitor-corp", "limit": 100},
            tool_name="ReadOrders"
        )


def test_tenant_guard_sets_tenant_if_missing():
    """Test tenant guard sets tenant if missing."""
    guard = TenantGuard()
    
    safe_params = guard.enforce_tenant_isolation(
        request_tenant_id="acme-corp",
        query_params={"limit": 100},
        tool_name="ReadOrders"
    )
    
    assert safe_params["tenant_id"] == "acme-corp"


def test_tenant_guard_filters_results():
    """Test tenant guard filters results."""
    guard = TenantGuard()
    
    results = [
        {"id": 1, "tenant_id": "acme-corp", "data": "data1"},
        {"id": 2, "tenant_id": "competitor-corp", "data": "data2"},
        {"id": 3, "tenant_id": "acme-corp", "data": "data3"}
    ]
    
    filtered = guard.filter_results_by_tenant(results, "acme-corp")
    
    assert len(filtered) == 2
    assert all(r["tenant_id"] == "acme-corp" for r in filtered)

