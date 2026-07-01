"""
Tenant routing middleware for cell-based SaaS architecture.

This module provides the routing logic that maps tenant_id to cell_id
at request time. It supports both Redis caching and direct registry lookup.

Based on the Node.js middleware in the article.
"""

import os
import json
import time
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class TenantCellMapping:
    """Represents the mapping between a tenant and its assigned cell."""
    tenant_id: str
    cell_id: str
    region: str
    status: str = "active"


# Simulated tenant registry (in production, this would query PostgreSQL/DynamoDB)
# This simulates the in-memory map from the Node.js example.
_TENANT_REGISTRY: Dict[str, TenantCellMapping] = {
    "t_001": TenantCellMapping(tenant_id="t_001", cell_id="cell-a", region="us-east"),
    "t_002": TenantCellMapping(tenant_id="t_002", cell_id="cell-b", region="eu-west"),
    "t_003": TenantCellMapping(tenant_id="t_003", cell_id="cell-c", region="apac", status="suspended"),
}

# Simulated Redis cache (in production, use real Redis client)
_cache_store: Dict[str, str] = {}
_cache_expiry: Dict[str, float] = {}


def _cache_get(key: str) -> Optional[str]:
    """Get from cache if not expired."""
    if key in _cache_expiry and time.time() < _cache_expiry[key]:
        return _cache_store.get(key)
    return None


def _cache_setex(key: str, ttl: int, value: str) -> None:
    """Set cache with TTL in seconds."""
    _cache_store[key] = value
    _cache_expiry[key] = time.time() + ttl


def get_tenant_cell(tenant_id: str) -> Optional[TenantCellMapping]:
    """
    Resolve tenant_id to cell mapping.
    
    In production:
    - Try cache first (Redis)
    - Fall back to registry database (PostgreSQL/DynamoDB)
    - Cache with short TTL (30 seconds) for quick propagation
    
    Args:
        tenant_id: The tenant identifier from request/JWT
        
    Returns:
        TenantCellMapping if found, None otherwise
    """
    # Try cache first (simulated)
    cached = _cache_get(f"tenant:{tenant_id}:cell")
    if cached:
        return TenantCellMapping(**json.loads(cached))
    
    # Fall back to registry
    mapping = _TENANT_REGISTRY.get(tenant_id)
    if not mapping:
        return None
    
    # Cache with short TTL
    _cache_setex(f"tenant:{tenant_id}:cell", 30, json.dumps({
        "tenant_id": mapping.tenant_id,
        "cell_id": mapping.cell_id,
        "region": mapping.region,
        "status": mapping.status,
    }))
    
    return mapping


def extract_cell_info(tenant_id: str) -> Dict[str, Any]:
    """
    Extract cell information for a tenant.
    
    This is the main routing function used by the middleware.
    
    Args:
        tenant_id: The tenant identifier
        
    Returns:
        Dict with cell_id, region, and status
    """
    mapping = get_tenant_cell(tenant_id)
    
    if not mapping:
        return {"error": "Tenant not found"}
    
    if mapping.status == "suspended":
        return {"error": "Tenant suspended", "status": mapping.status}
    
    return {
        "tenant_id": mapping.tenant_id,
        "cell_id": mapping.cell_id,
        "region": mapping.region,
        "status": mapping.status,
    }


class RoutingMiddleware:
    """
    Express-style middleware for tenant-to-cell routing.
    
    Usage:
        app.use(routing_middleware)
        # req.tenant contains { id, cellId, region }
    """
    
    def __init__(self, is_cell_router: bool = False):
        self.is_cell_router = is_cell_router
    
    async def __call__(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process request and attach tenant/cell context.
        
        Args:
            request: Request dict with headers
            
        Returns:
            Response dict or raises error
        """
        # Extract tenant_id from header, JWT, or subdomain
        tenant_id = (
            request.get("headers", {}).get("x-tenant-id")
            or request.get("jwt", {}).get("tenant_id")
            or request.get("subdomain")
        )
        
        if not tenant_id:
            return {"status": 400, "error": "Missing tenant_id"}
        
        cell_info = extract_cell_info(tenant_id)
        
        if "error" in cell_info:
            if cell_info.get("status") == "suspended":
                return {"status": 403, "error": "Tenant account is suspended"}
            return {"status": 404, "error": "Tenant not found"}
        
        # Attach cell info to request context
        request["tenant"] = {
            "id": tenant_id,
            "cellId": cell_info["cell_id"],
            "region": cell_info["region"],
        }
        
        # If this is a global router, set the target cell URL
        if self.is_cell_router:
            request["cell_target_url"] = (
                f"https://{cell_info['cell_id']}.{cell_info['region']}.internal:3000"
                f"{request.get('path', '/')}"
            )
        
        return {"status": 200, "continue": True}


def build_jwt_claims(tenant_id: str, cell_id: str, region: str) -> Dict[str, Any]:
    """
    Build JWT claims with embedded cell_id for edge routing.
    
    This allows routing without registry lookup at the edge.
    Tokens should have short expiry (15-30 min) for quick propagation.
    
    Args:
        tenant_id: Tenant identifier
        cell_id: Cell identifier
        region: Region identifier
        
    Returns:
        JWT claims dict
    """
    return {
        "sub": f"user_{tenant_id}",
        "tenant_id": tenant_id,
        "cell_id": cell_id,
        "region": region,
        "exp": int(time.time()) + (30 * 60),  # 30 minutes expiry
    }