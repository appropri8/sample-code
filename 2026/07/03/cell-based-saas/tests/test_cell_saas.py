"""
Tests for cell-based SaaS sample code.
"""

import pytest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tenant_routing import (
    get_tenant_cell,
    extract_cell_info,
    RoutingMiddleware,
    build_jwt_claims,
)
from registry import TenantRegistry, TenantStatus, MigrationState, get_registry_client
from telemetry import TelemetrySetup, setup_cell_telemetry
from deployment import DeploymentManager, CellDeploymentConfig


class TestTenantRouting:
    """Tests for tenant routing module."""
    
    def test_get_tenant_cell_returns_mapping(self):
        """Test that valid tenant returns cell mapping."""
        result = get_tenant_cell("t_001")
        assert result is not None
        assert result.tenant_id == "t_001"
        assert result.cell_id == "cell-a"
        assert result.region == "us-east"
    
    def test_get_tenant_cell_unknown_returns_none(self):
        """Test that unknown tenant returns None."""
        result = get_tenant_cell("unknown_tenant")
        assert result is None
    
    def test_extract_cell_info_success(self):
        """Test extract_cell_info for valid tenant."""
        result = extract_cell_info("t_002")
        assert result["tenant_id"] == "t_002"
        assert result["cell_id"] == "cell-b"
    
    def test_extract_cell_info_suspended_tenant(self):
        """Test that suspended tenant returns error."""
        result = extract_cell_info("t_003")
        assert "error" in result
        assert result["status"] == "suspended"
    
    def test_extract_cell_info_unknown_tenant(self):
        """Test that unknown tenant returns error."""
        result = extract_cell_info("nonexistent")
        assert "error" in result
    
    def test_build_jwt_claims(self):
        """Test JWT claim generation."""
        claims = build_jwt_claims("t_001", "cell-a", "us-east")
        assert claims["tenant_id"] == "t_001"
        assert claims["cell_id"] == "cell-a"
        assert claims["region"] == "us-east"
        assert "exp" in claims


class TestRoutingMiddleware:
    """Tests for routing middleware."""
    
    def test_middleware_valid_tenant(self):
        """Test middleware processes valid tenant."""
        middleware = RoutingMiddleware(is_cell_router=False)
        request = {
            "headers": {"x-tenant-id": "t_001"},
            "path": "/api/v1/users",
        }
        result = middleware.__call__(request)
        assert result["continue"] is True
        assert request["tenant"]["id"] == "t_001"
        assert request["tenant"]["cellId"] == "cell-a"
    
    def test_middleware_missing_tenant(self):
        """Test middleware rejects missing tenant."""
        middleware = RoutingMiddleware()
        request = {"path": "/api/v1/users"}
        result = middleware.__call__(request)
        assert result["status"] == 400
    
    def test_middleware_suspended_tenant(self):
        """Test middleware rejects suspended tenant."""
        middleware = RoutingMiddleware()
        request = {"headers": {"x-tenant-id": "t_003"}}
        result = middleware.__call__(request)
        assert result["status"] == 403


class TestTenantRegistry:
    """Tests for tenant registry."""
    
    def test_create_and_get_tenant(self):
        """Test creating and retrieving tenant."""
        registry = TenantRegistry()
        record = registry.create_tenant("new_tenant", "cell-a", "us-east")
        assert record.tenant_id == "new_tenant"
        
        fetched = registry.get_tenant("new_tenant")
        assert fetched == record
    
    def test_update_with_optimistic_concurrency(self):
        """Test that version mismatch prevents update."""
        registry = TenantRegistry()
        registry.create_tenant("tenant_x", "cell-a", "us-east")
        
        # Try to update with wrong version
        result = registry.update_tenant(
            "tenant_x",
            cell_id="cell-b",
            version=999,  # Wrong version
        )
        assert result is False
        
        # Correct version should work
        record = registry.get_tenant("tenant_x")
        result = registry.update_tenant(
            "tenant_x",
            cell_id="cell-b",
            version=record.version,
        )
        assert result is True
    
    def test_migration_state_updates(self):
        """Test migration state transitions."""
        registry = TenantRegistry()
        registry.create_tenant("migrating_tenant", "cell-a", "us-east")
        
        record = registry.get_tenant("migrating_tenant")
        registry.update_tenant(
            "migrating_tenant",
            migration_state=MigrationState.DRAINING,
            version=record.version,
        )
        
        updated = registry.get_tenant("migrating_tenant")
        assert updated.migration_state == MigrationState.DRAINING


class TestTelemetry:
    """Tests for telemetry module."""
    
    def test_create_span_with_attributes(self):
        """Test span creation with cell/tenant attributes."""
        telemetry = TelemetrySetup(
            service_name="test-service",
            cell_id="cell-a",
            region="us-east",
            deployment_version="v1.0.0",
        )
        
        span = telemetry.create_span(
            "test-span",
            {"tenant.id": "t_001"},
        )
        
        assert span.cell_id == "cell-a"
        assert span.tenant_id == "t_001"
        assert span.deployment_version == "v1.0.0"
    
    def test_record_request_metrics(self):
        """Test request metric recording."""
        telemetry = TelemetrySetup(
            service_name="test-service",
            cell_id="cell-a",
            region="us-east",
            deployment_version="v1.0.0",
        )
        
        telemetry.record_request("GET", "/api/users", 200, 150, "t_001")
        
        metrics = telemetry.get_metrics()
        assert len(metrics) == 1
        assert metrics[0]["name"] == "cell.requests.total"
        assert metrics[0]["attributes"]["tenant.id"] == "t_001"
        assert metrics[0]["attributes"]["cell.id"] == "cell-a"


class TestDeployment:
    """Tests for deployment module."""
    
    def test_deploy_success(self):
        """Test successful deployment to cell."""
        manager = DeploymentManager()
        config = CellDeploymentConfig(
            cell_id="cell-a",
            region="us-east",
            version="v1.0.0",
        )
        
        result = manager.deploy_to_cell(config)
        assert result is True
        assert "cell-a" in manager.deployed_cells
    
    def test_rollout_to_cells(self):
        """Test sequential rollout to multiple cells."""
        from deployment import rollout_to_cells
        
        rollout_to_cells(["cell-a", "cell-b"], "v2.0.0")
        
        manager = get_deployment_manager()
        assert "cell-a" in manager.deployed_cells
        assert "cell-b" in manager.deployed_cells


if __name__ == "__main__":
    pytest.main([__file__, "-v"])