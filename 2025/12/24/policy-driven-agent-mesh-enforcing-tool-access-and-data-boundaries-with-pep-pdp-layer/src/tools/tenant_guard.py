"""Tenant guard for enforcing tenant isolation."""
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class TenantGuard:
    """Tenant guard for enforcing tenant isolation."""
    
    def __init__(self):
        """Initialize tenant guard."""
        pass
    
    def enforce_tenant_isolation(
        self,
        request_tenant_id: str,
        query_params: Dict[str, Any],
        tool_name: str
    ) -> Dict[str, Any]:
        """Enforce tenant isolation in tool calls.
        
        Args:
            request_tenant_id: Tenant ID from request
            query_params: Query parameters
            tool_name: Tool name (for logging)
            
        Returns:
            Safe query parameters with tenant filter applied
            
        Raises:
            PermissionError: If cross-tenant access is attempted
        """
        # Extract tenant from query params
        query_tenant = query_params.get("tenant_id")
        
        # If tenant is specified in query, it must match request tenant
        if query_tenant and query_tenant != request_tenant_id:
            raise PermissionError(
                f"Cross-tenant access denied: request tenant {request_tenant_id} "
                f"does not match query tenant {query_tenant}"
            )
        
        # Always set tenant filter to request tenant
        safe_params = query_params.copy()
        safe_params["tenant_id"] = request_tenant_id
        
        return safe_params
    
    def filter_results_by_tenant(
        self,
        results: List[Dict[str, Any]],
        tenant_id: str,
        tenant_field: str = "tenant_id"
    ) -> List[Dict[str, Any]]:
        """Filter results to ensure tenant isolation.
        
        Args:
            results: List of result records
            tenant_id: Expected tenant ID
            tenant_field: Field name for tenant ID (default: "tenant_id")
            
        Returns:
            Filtered results containing only records for the specified tenant
        """
        filtered = [
            record for record in results
            if record.get(tenant_field) == tenant_id
        ]
        
        # Log if filtering removed records (potential data leak)
        if len(filtered) < len(results):
            logger.warning(
                f"Tenant guard filtered {len(results) - len(filtered)} records "
                f"that did not match tenant {tenant_id}"
            )
        
        return filtered

